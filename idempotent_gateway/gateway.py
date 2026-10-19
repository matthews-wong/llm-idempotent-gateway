"""At-most-once LLM calls keyed by a caller-supplied idempotency key."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable

from .fingerprint import fingerprint
from .provider import Provider, Request, Response

DEFAULT_TTL_SECONDS = 24 * 60 * 60


class IdempotencyConflict(Exception):
    """The key was already used for a different request."""

    def __init__(self, key: str) -> None:
        super().__init__(f"idempotency key {key!r} was already used with a different request")
        self.key = key


@dataclass
class _Entry:
    fingerprint: str
    expires_at: float
    done: threading.Event
    response: Response | None = None


class Gateway:
    def __init__(
        self,
        provider: Provider,
        *,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._provider = provider
        self._ttl = ttl_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._entries: dict[str, _Entry] = {}

    def complete(self, request: Request, idempotency_key: str) -> Response:
        digest = fingerprint(request)
        with self._lock:
            entry = self._entries.get(idempotency_key)
            if entry is not None and entry.response is not None and entry.expires_at <= self._clock():
                entry = None
            if entry is None:
                entry = _Entry(digest, self._clock() + self._ttl, threading.Event())
                self._entries[idempotency_key] = entry
                owner = True
            else:
                owner = False
            if entry.fingerprint != digest:
                raise IdempotencyConflict(idempotency_key)

        if owner:
            return self._call(entry, request, idempotency_key)

        entry.done.wait()
        if entry.response is not None:
            return entry.response
        # The in-flight call failed and was dropped; this caller retries it.
        return self.complete(request, idempotency_key)

    def _call(self, entry: _Entry, request: Request, key: str) -> Response:
        try:
            entry.response = self._provider.complete(request)
        except BaseException:
            with self._lock:
                # Failures are not stored: a retry with the same key must reach the provider.
                if self._entries.get(key) is entry:
                    del self._entries[key]
            raise
        finally:
            # Set after the response is stored, so waiters never see a half-finished entry.
            entry.done.set()
        return entry.response

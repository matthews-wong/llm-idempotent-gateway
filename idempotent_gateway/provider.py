"""The seam every model call goes through, plus a deterministic fake."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol


@dataclass(frozen=True)
class Request:
    model: str
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.0


@dataclass(frozen=True)
class Response:
    text: str
    input_tokens: int
    output_tokens: int


class ProviderError(Exception):
    """Raised by a provider when a call fails."""


class Provider(Protocol):
    def complete(self, request: Request) -> Response: ...


@dataclass
class FakeProvider:
    """Echoes the prompt; `fail_first` makes the first N calls raise."""

    fail_first: int = 0
    on_call: Callable[[Request], None] | None = None
    calls: int = field(default=0, init=False)

    def complete(self, request: Request) -> Response:
        self.calls += 1
        if self.on_call is not None:
            self.on_call(request)
        if self.calls <= self.fail_first:
            raise ProviderError(f"scripted failure on call {self.calls}")
        words = request.prompt.split()
        return Response(
            text=f"echo: {request.prompt}",
            input_tokens=len(words),
            output_tokens=len(words) + 1,
        )

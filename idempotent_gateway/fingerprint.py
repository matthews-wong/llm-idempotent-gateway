"""Stable request fingerprints, used to detect a key reused for a different request."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from .provider import Request


def fingerprint(request: Request) -> str:
    # sort_keys + fixed separators keep the digest independent of field order.
    canonical = json.dumps(asdict(request), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

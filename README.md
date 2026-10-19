# llm-idempotent-gateway

A small gateway wrapper that makes LLM calls safe to retry. Callers pass an
idempotency key; the gateway guarantees the provider is invoked at most once per
key and replays the stored response for every repeat.

Pure Python standard library, no network and no API key needed: the tests and the
example run against a deterministic fake provider.

## Behaviour

- Same key, same request: the stored response is replayed, the provider is not called.
- Same key, different request: rejected with `IdempotencyConflict` instead of
  silently returning an answer to a different question.
- Same key while the first call is still running: the second caller waits for that
  call and shares its result.
- A failed call is not stored, so a retry with the same key reaches the provider again.
- Stored entries expire after a TTL.

## Usage

```python
from idempotent_gateway.gateway import Gateway
from idempotent_gateway.provider import FakeProvider, Request

gateway = Gateway(FakeProvider(), ttl_seconds=3600)
reply = gateway.complete(Request(model="m", prompt="hi"), idempotency_key="order-1042")
```

Any object with `complete(request) -> Response` can replace `FakeProvider`.

## Validate

```
python3 -m unittest -v
python3 examples/retry_storm.py
```

The example retries one request five times against the fake provider: 5 provider
calls without the gateway, 1 with it. That is a fixture run, not a measurement of a
real model.

## Limits

- The store is in memory and per process; a restart forgets every key.
- Keys are scoped to the whole gateway, not to a caller. Prefix them per tenant.
- Expired entries are dropped lazily when their key is reused, so a long-lived
  process with many one-off keys will keep growing.

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

## Status

Scaffolding. The core, tests and an example follow.

import threading
import unittest

from idempotent_gateway.gateway import Gateway, IdempotencyConflict
from idempotent_gateway.provider import FakeProvider, ProviderError, Request

REQ = Request(model="m", prompt="hello world")


class ReplayTests(unittest.TestCase):
    def test_repeat_key_replays_without_calling_provider(self):
        provider = FakeProvider()
        gateway = Gateway(provider)
        first = gateway.complete(REQ, "k1")
        second = gateway.complete(REQ, "k1")
        self.assertEqual(first, second)
        self.assertEqual(provider.calls, 1)

    def test_different_keys_call_provider_each_time(self):
        provider = FakeProvider()
        gateway = Gateway(provider)
        gateway.complete(REQ, "a")
        gateway.complete(REQ, "b")
        self.assertEqual(provider.calls, 2)

    def test_key_reuse_with_other_request_conflicts(self):
        gateway = Gateway(FakeProvider())
        gateway.complete(REQ, "k1")
        with self.assertRaisesRegex(IdempotencyConflict, "'k1'"):
            gateway.complete(Request(model="m", prompt="other"), "k1")

    def test_failure_is_not_stored(self):
        provider = FakeProvider(fail_first=1)
        gateway = Gateway(provider)
        with self.assertRaises(ProviderError):
            gateway.complete(REQ, "k1")
        self.assertEqual(gateway.complete(REQ, "k1").text, "echo: hello world")
        self.assertEqual(provider.calls, 2)

    def test_entry_expires_after_ttl(self):
        now = [0.0]
        provider = FakeProvider()
        gateway = Gateway(provider, ttl_seconds=10, clock=lambda: now[0])
        gateway.complete(REQ, "k1")
        now[0] = 11.0
        gateway.complete(REQ, "k1")
        self.assertEqual(provider.calls, 2)


class ConcurrencyTests(unittest.TestCase):
    def test_concurrent_same_key_calls_provider_once(self):
        release = threading.Event()
        started = threading.Event()

        def block(_request):
            started.set()
            release.wait(timeout=5)

        provider = FakeProvider(on_call=block)
        gateway = Gateway(provider)
        results = []
        threads = [
            threading.Thread(target=lambda: results.append(gateway.complete(REQ, "k1")))
            for _ in range(5)
        ]
        for t in threads:
            t.start()
        self.assertTrue(started.wait(timeout=5))
        release.set()
        for t in threads:
            t.join(timeout=5)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(len(results), 5)
        self.assertEqual(len(set(results)), 1)


if __name__ == "__main__":
    unittest.main()

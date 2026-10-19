import unittest

from idempotent_gateway.fingerprint import fingerprint
from idempotent_gateway.provider import Request


class FingerprintTests(unittest.TestCase):
    def test_equal_requests_share_a_digest(self):
        self.assertEqual(
            fingerprint(Request(model="m", prompt="p")),
            fingerprint(Request(prompt="p", model="m")),
        )

    def test_each_field_changes_the_digest(self):
        base = Request(model="m", prompt="p")
        variants = [
            Request(model="n", prompt="p"),
            Request(model="m", prompt="q"),
            Request(model="m", prompt="p", max_tokens=1),
            Request(model="m", prompt="p", temperature=0.5),
        ]
        digests = {fingerprint(r) for r in [base, *variants]}
        self.assertEqual(len(digests), 5)


if __name__ == "__main__":
    unittest.main()

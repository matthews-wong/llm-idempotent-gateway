"""A client that retries one logical request 5 times, with and without the gateway."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from idempotent_gateway.gateway import Gateway
from idempotent_gateway.provider import FakeProvider, Request

RETRIES = 5
REQUEST = Request(model="demo-model", prompt="summarise the incident report")


def main() -> None:
    bare = FakeProvider()
    for _ in range(RETRIES):
        bare.complete(REQUEST)

    guarded = FakeProvider()
    gateway = Gateway(guarded)
    for _ in range(RETRIES):
        gateway.complete(REQUEST, idempotency_key="order-1042")

    print(f"{RETRIES} client retries, fake provider")
    print(f"  without gateway: {bare.calls} provider calls")
    print(f"  with gateway:    {guarded.calls} provider call")


if __name__ == "__main__":
    main()

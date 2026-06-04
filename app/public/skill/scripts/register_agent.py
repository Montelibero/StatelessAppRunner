#!/usr/bin/env python3
"""Register an agent and print ready API calls.

No external dependencies required.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from urllib import request


def b32_no_pad(data: bytes) -> str:
    return base64.b32encode(data).decode("utf-8").rstrip("=")


def derive_agent_id(agent_secret: str) -> str:
    digest = hashlib.sha256(agent_secret.encode("utf-8")).digest()
    body = b32_no_pad(digest)
    return f"MTLA{body[4:]}"


def new_secret() -> str:
    raw = os.urandom(18)
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def fetch_pow_challenge(base_url: str) -> dict:
    req = request.Request(
        f"{base_url}/api/agent/register/challenge",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def register(
    base_url: str,
    agent_secret: str,
    pow_challenge: str,
    pow_nonce: str,
    agent_name: str,
) -> dict:
    payload = {
        "agent_secret": agent_secret,
        "pow_challenge": pow_challenge,
        "pow_nonce": pow_nonce,
        "agent_name": agent_name,
        "client": "python",
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{base_url}/api/agent/register",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _leading_zero_bits(data: bytes) -> int:
    bits = 0
    for b in data:
        if b == 0:
            bits += 8
            continue
        return bits + (8 - b.bit_length())
    return bits


def _b64url_decode(value: str) -> bytes:
    pad = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + pad).encode("utf-8"))


def pow_bits_from_challenge(challenge: str) -> int:
    payload_b64 = challenge.split(".", 1)[0]
    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    return int(payload["b"])


def solve_registration_pow(
    secret: str, challenge: str, bits: int
) -> tuple[str, int, float]:
    payload_b64 = challenge.split(".", 1)[0]
    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    seed = str(payload["n"])
    started_at = time.monotonic()
    tries = 0
    nonce = 0
    while True:
        tries += 1
        nonce += 1
        nonce_s = str(nonce)
        digest = hashlib.sha256(f"{seed}:{secret}:{nonce_s}".encode("utf-8")).digest()
        if _leading_zero_bits(digest) >= bits:
            break
    return nonce_s, tries, time.monotonic() - started_at


def main() -> None:
    base_url = os.getenv("APP_BASE_URL", "https://mtlminiapps.us").rstrip("/")
    agent_name = os.getenv("AGENT_NAME", "agent-python")
    agent_secret = new_secret()
    challenge = fetch_pow_challenge(base_url)
    pow_challenge = challenge["pow_challenge"]
    bits = pow_bits_from_challenge(pow_challenge)
    pow_nonce, pow_tries, pow_elapsed = solve_registration_pow(
        agent_secret, pow_challenge, bits
    )
    print(
        f"Registration PoW solved in {pow_tries} tries ({pow_elapsed:.1f}s), nonce={pow_nonce}"
    )
    result = register(base_url, agent_secret, pow_challenge, pow_nonce, agent_name)
    bearer_token = result["bearer_token"]

    print("\nagent_id:", result["agent_id"])
    print("bearer_token:", bearer_token)

    print("\nDefault mode example:")
    print(
        "curl -X POST "
        f"{base_url}/api/agent/generate "
        "-H 'Content-Type: application/json' "
        f"-H 'Authorization: Bearer {bearer_token}' "
        '-d \'{"html":"<h1>Hello</h1>"}\''
    )

    print("\nOptional persistent mode example:")
    print(
        "curl -X POST "
        f"{base_url}/api/agent/apps "
        "-H 'Content-Type: application/json' "
        f"-H 'Authorization: Bearer {bearer_token}' "
        '-d \'{"html":"<h1>Saved</h1>"}\''
    )


if __name__ == "__main__":
    main()

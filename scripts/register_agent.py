#!/usr/bin/env python3
"""Register an agent and print ready API calls.

No external dependencies required.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from urllib import request


def b32_no_pad(data: bytes) -> str:
    return base64.b32encode(data).decode("utf-8").rstrip("=")


def derive_agent_id(agent_secret: str) -> str:
    digest = hashlib.sha256(agent_secret.encode("utf-8")).digest()
    return b32_no_pad(digest)


def challenge_ok(agent_id: str) -> bool:
    return agent_id.endswith("MTL") and len(agent_id) >= 8 and agent_id[:8].isalpha()


def new_secret() -> str:
    raw = os.urandom(18)
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def register(base_url: str, agent_secret: str, agent_name: str) -> dict:
    payload = {
        "agent_secret": agent_secret,
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


def main() -> None:
    base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    agent_name = os.getenv("AGENT_NAME", "agent-python")

    tries = 0
    while True:
        tries += 1
        agent_secret = new_secret()
        agent_id = derive_agent_id(agent_secret)
        if challenge_ok(agent_id):
            break

    print(f"Challenge solved in {tries} tries")
    result = register(base_url, agent_secret, agent_name)
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

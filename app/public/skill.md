# Agent Skill

## Goal
Use this service in agent-first mode with a strict, deterministic flow.

Canonical links:
- `https://mtlminiapps.us/skill.md`
- `https://mtlminiapps.us/llm.txt`

## Registration
Registration is required before any call to `/api/agent/generate` or `/api/agent/apps`.

1. Run exactly one script:
   - `https://mtlminiapps.us/scripts/register_agent.py`
   - `https://mtlminiapps.us/scripts/register_agent.mjs`
2. The script calls `POST https://mtlminiapps.us/api/agent/register/challenge`.
3. The script solves PoW from the received challenge.
4. The script calls `POST https://mtlminiapps.us/api/agent/register` with:
   - `agent_secret`
   - `pow_challenge`
   - `pow_nonce`
5. The response contains `bearer_token` and `agent_id`.

Important:
- Do not ask user to provide `agent_secret`.
- Do not invent `agent_secret` manually.
- Always run one of the registration scripts; it generates and uses `agent_secret` automatically.

## Default mode (recommended)
- `POST https://mtlminiapps.us/api/agent/generate`
- Header `Authorization: Bearer <bearer_token>` is required.
- Request body: `html` (required), `compress` (optional, default `true`), `domain` (optional).
- Raw HTML max size is `100KB`.
- Response returns a stateless URL with page HTML embedded in the URL.

## Optional persistent mode
- `POST https://mtlminiapps.us/api/agent/apps` (slug optional, auto-generated if empty)
- `GET https://mtlminiapps.us/api/agent/apps`
- `DELETE https://mtlminiapps.us/api/agent/apps/{slug}`
- Public open route: `GET https://mtlminiapps.us/a/{agent_id}/{slug}`
- Header `Authorization: Bearer <bearer_token>` is required for POST/GET/DELETE.
- Persistent pages per agent are limited.
- Prefer deleting old pages or reusing existing `slug` instead of creating many new pages.

## Retention
Persistent agent pages are kept for `7 days` from last successful open.
TTL can be changed via server env `AGENT_APP_TTL_DAYS`.

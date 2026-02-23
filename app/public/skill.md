# Agent Skill

## Goal
Use this service in agent-first mode.

Canonical links:
- `https://mtlminiapps.us/skill.md`
- `https://mtlminiapps.us/llm.txt`

## Registration
1. Download and run one script:
   - `https://mtlminiapps.us/scripts/register_agent.py`
   - `https://mtlminiapps.us/scripts/register_agent.mjs`
2. Script solves challenge and calls `POST https://mtlminiapps.us/api/agent/register`.
3. Script prints `bearer_token` and ready API commands.

Important:
- Do not ask user to provide `agent_secret`.
- Do not invent `agent_secret` manually.
- Always run one of the registration scripts; the script generates and uses `agent_secret` automatically.

## Default mode (recommended)
- `POST https://mtlminiapps.us/api/agent/generate`
- Bearer auth required.
- `compress` is optional, default is `true`.
- Raw HTML max size: `100KB`.

## Optional persistent mode
- `POST https://mtlminiapps.us/api/agent/apps` (slug optional, auto-generated if empty)
- `GET https://mtlminiapps.us/api/agent/apps`
- `DELETE https://mtlminiapps.us/api/agent/apps/{slug}`
- Public open route: `GET https://mtlminiapps.us/a/{agent_id}/{slug}`

## Retention
Persistent agent pages are kept for `7 days` from last successful open.
TTL can be changed via server env `AGENT_APP_TTL_DAYS`.

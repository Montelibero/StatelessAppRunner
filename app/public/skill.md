# Agent Skill

## Goal
Use this service in agent-first mode.

## Registration
1. Download and run one script:
   - `/scripts/register_agent.py`
   - `/scripts/register_agent.mjs`
2. Script solves challenge and calls `POST /api/agent/register`.
3. Script prints `bearer_token` and ready API commands.

## Default mode (recommended)
- `POST /api/agent/generate`
- Bearer auth required.
- `compress` is optional, default is `true`.
- Raw HTML max size: `100KB`.

## Optional persistent mode
- `POST /api/agent/apps` (slug optional, auto-generated if empty)
- `GET /api/agent/apps`
- `DELETE /api/agent/apps/{slug}`
- Public open route: `GET /a/{agent_id}/{slug}`

## Retention
Persistent agent pages are kept for `7 days` from last successful open.
TTL can be changed via server env `AGENT_APP_TTL_DAYS`.

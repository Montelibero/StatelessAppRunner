---
name: stateless-app-runner
description: Publish agent-created HTML pages as shareable links via mtlminiapps.us — stateless (HTML embedded in the URL) or persistent (HTML stored on the server). Use when an agent needs to turn HTML into a public URL.
---

# Agent Skill

## Goal
Use this service in agent-first mode with a strict, deterministic flow.

Canonical links:
- `https://mtlminiapps.us/skill.md`
- `https://mtlminiapps.us/llm.txt`
- Fallback API schema (external API only): `https://mtlminiapps.us/openapi.json`
- By using the service, you agree to Terms: `https://mtlminiapps.us/terms`
- Do not use for illegal activity, spam, fraud, deception, or malware; access may be suspended or banned.

## Registration
Registration is required before any call to `/api/agent/generate` or `/api/agent/apps`.

1. Run exactly one script (when installed as a skill, use the bundled copy in `scripts/`; otherwise fetch by URL):
   - `scripts/register_agent.py` (or `https://mtlminiapps.us/scripts/register_agent.py`)
   - `scripts/register_agent.mjs` (or `https://mtlminiapps.us/scripts/register_agent.mjs`)
2. The script calls `POST https://mtlminiapps.us/api/agent/register/challenge`.
3. The script solves PoW from the received challenge.
4. The script calls `POST https://mtlminiapps.us/api/agent/register` with:
   - `agent_secret`
   - `pow_challenge`
   - `pow_nonce` (string)
   - `agent_name` (optional string)
   - `client` (optional string, for client label)
5. The response contains `bearer_token` and `agent_id`.

Important:
- Do not ask user to provide `agent_secret`.
- Do not invent `agent_secret` manually.
- Always run one of the registration scripts; it generates and uses `agent_secret` automatically.

## Default mode (recommended)
- `POST https://mtlminiapps.us/api/agent/generate`
- Header `Authorization: Bearer <bearer_token>` is required.
- Request body: `html` (required), `compress` (optional, default `true`), `domain` (optional).
- `html` must be a non-empty UTF-8 string.
- Raw HTML max size is `100KB`.
- `domain` overrides returned link host. If omitted, service default domain is used.
- Response returns a stateless URL with page HTML embedded in the URL.

## Optional persistent mode
- `POST https://mtlminiapps.us/api/agent/apps` (slug optional, auto-generated if empty)
- `GET https://mtlminiapps.us/api/agent/apps`
- `DELETE https://mtlminiapps.us/api/agent/apps/{slug}`
- Public open route: `GET https://mtlminiapps.us/a/{agent_id}/{slug}`
- Header `Authorization: Bearer <bearer_token>` is required for POST/GET/DELETE.
- Use header `Content-Type: application/json` for POST.
- POST body is JSON:
  - `html` (required): non-empty string with raw page HTML (UTF-8 text), max `100KB`.
  - `slug` (optional): string for custom short URL; if omitted or empty, server generates slug.
- Example body:
  - `{"html":"<h1>Hello</h1><script>console.log('ok')</script>","slug":"demo-app"}`
- Persistent pages per agent are limited.
- Prefer deleting old pages or reusing existing `slug` instead of creating many new pages.

## Rate limits
- New persistent pages (`POST /api/agent/apps` with new slug):
  - max `5` per minute
  - max `20` per hour
  - max `40` per day
- Persistent edits (`POST /api/agent/apps` for existing slug):
  - max `5` updates per minute
- Total persistent pages per agent:
  - max `80`

Note:
- Public API `POST /api/generate` has `compress` default `false`.
- Agent API `POST /api/agent/generate` has `compress` default `true`.

## Retention
Persistent agent pages are kept for `7 days` from last successful open.
TTL can be changed via server env `AGENT_APP_TTL_DAYS`.

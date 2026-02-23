# Agent-First Homepage + Agent API Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an agent-first public flow (homepage, onboarding artifacts, bearer API) while preserving existing keys/routes and adding agent page TTL policy configurable via environment.

**Architecture:** Keep current FastAPI + FastHTML layers and existing `/`, `/p*`, `/api/*` contracts intact for backward compatibility. Add a parallel `agent` capability with additive DB tables, new `/api/agent/*` endpoints, and a new public route namespace for agent-owned persistent pages. Keep all behavior changes behind new routes/features, not by mutating legacy contracts.

**Tech Stack:** FastAPI, python-fasthtml, sqlite3, pytest, pyright, ruff, uv

---

### Task 1: Add homepage tests for agent-first content and no admin mention

**Files:**
- Modify: `tests/test_ui_pages.py`
- Modify: `tests/test_homepage.py`
- Test: `tests/test_ui_pages.py`
- Test: `tests/test_homepage.py`

**Step 1: Write the failing tests**
- Add assertions for homepage text blocks:
  - "Если вы агент" block exists and is visually first.
  - "Если вы человек" block exists and instructs to pass the service link to an AI agent.
  - No `/admin` link in homepage markup.
  - Links to `skill.md` and registration scripts are present.

**Step 2: Run test to verify it fails**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_ui_pages.py tests/test_homepage.py`
- Expected: FAIL due to missing new homepage content/links.

**Step 3: Write minimal implementation**
- Update `app/ui/pages.py::render_home_page` to new two-block layout:
  - Agent block on top.
  - Human block with instruction to share the link with an agent.
  - Remove explicit admin entry from homepage.

**Step 4: Run tests to verify they pass**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_ui_pages.py tests/test_homepage.py`
- Expected: PASS.

**Step 5: Commit**
```bash
git add tests/test_ui_pages.py tests/test_homepage.py app/ui/pages.py
git commit -m "feat: switch homepage to agent-first onboarding"
```

### Task 2: Add failing tests for static onboarding artifacts (`/skill.md`, `/llm.txt`, scripts)

**Files:**
- Create: `tests/test_agent_onboarding_assets.py`
- Create: `app/public/skill.md`
- Create: `app/public/llm.txt`
- Create: `scripts/register_agent.py`
- Create: `scripts/register_agent.mjs`
- Modify: `app/interface/routes.py`

**Step 1: Write the failing tests**
- Add tests for endpoints/files:
  - `GET /skill.md` returns markdown with agent flow + API examples.
  - `GET /llm.txt` returns concise machine-readable agent instructions.
  - `GET /scripts/register_agent.py` and `GET /scripts/register_agent.mjs` return downloadable text.

**Step 2: Run test to verify it fails**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_onboarding_assets.py`
- Expected: FAIL due to missing routes/files.

**Step 3: Write minimal implementation**
- Add route handlers in `app/interface/routes.py` serving plain text from `app/public/*` and `scripts/*`.
- Add minimal `skill.md` and `llm.txt` content:
  - Default flow: `POST /api/agent/generate`.
  - Optional flow: persistent pages with slug.
  - Limits: raw HTML max 100KB.
  - TTL rule (7 days from last open).
- Add minimal script stubs (Python/Node) with shebang/usage headers and TODO placeholders for next tasks.

**Step 4: Run tests to verify they pass**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_onboarding_assets.py`
- Expected: PASS.

**Step 5: Commit**
```bash
git add tests/test_agent_onboarding_assets.py app/public/skill.md app/public/llm.txt scripts/register_agent.py scripts/register_agent.mjs app/interface/routes.py
git commit -m "feat: expose agent onboarding assets"
```

### Task 3: Add additive DB schema and tests for agents/tokens/apps

**Files:**
- Create: `tests_db/test_agent_schema.py`
- Modify: `app/db.py`
- Test: `tests_db/test_agent_schema.py`

**Step 1: Write the failing tests**
- Add schema tests ensuring migration creates additive tables:
  - `agents`
  - `agent_tokens`
  - `agent_apps`
- Assert legacy tables (`users`, `apps`) remain untouched and accessible.

**Step 2: Run test to verify it fails**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests_db/test_agent_schema.py`
- Expected: FAIL due to missing tables/columns/indexes.

**Step 3: Write minimal implementation**
- In `app/db.py`, extend initialization with additive `CREATE TABLE IF NOT EXISTS` and indexes.
- Add helper functions (minimal signatures only):
  - `create_or_get_agent(...)`
  - `issue_agent_token(...)`
  - `get_agent_by_token(...)`
  - `save_agent_app(...)`
  - `list_agent_apps(...)`
  - `get_agent_app(...)`
  - `delete_agent_app(...)`

**Step 4: Run tests to verify they pass**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests_db/test_agent_schema.py`
- Expected: PASS.

**Step 5: Commit**
```bash
git add tests_db/test_agent_schema.py app/db.py
git commit -m "feat: add additive sqlite schema for agent auth and apps"
```

### Task 4: Add failing tests for agent registration and bearer auth

**Files:**
- Create: `tests/test_agent_auth.py`
- Modify: `app/interface/routes.py`
- Modify: `app/db.py`

**Step 1: Write the failing tests**
- Add tests for `POST /api/agent/register`:
  - Success with valid `agent_secret` meeting rule.
  - Rejection when suffix/prefix challenge fails.
  - Response includes `agent_id`, `bearer_token`, `created`.
- Add tests for bearer guards:
  - Missing `Authorization` -> 401.
  - Invalid token -> 403.

**Step 2: Run test to verify it fails**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_auth.py`
- Expected: FAIL due to missing endpoint/auth flow.

**Step 3: Write minimal implementation**
- Implement challenge derivation in route/service:
  - `agent_id_base32 = base32(sha256(agent_secret))`.
  - Must `endswith("MTL")` and satisfy agreed prefix letters rule.
- On success issue bearer token (store hash only), return raw token once.
- Add shared bearer extractor/validator for agent endpoints.

**Step 4: Run tests to verify they pass**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_auth.py`
- Expected: PASS.

**Step 5: Commit**
```bash
git add tests/test_agent_auth.py app/interface/routes.py app/db.py
git commit -m "feat: add agent registration and bearer auth"
```

### Task 5: Add failing tests for default stateless endpoint `/api/agent/generate`

**Files:**
- Create: `tests/test_agent_generate.py`
- Modify: `app/interface/routes.py`
- Modify: `app/interface/schemas.py`

**Step 1: Write the failing tests**
- Add tests:
  - `POST /api/agent/generate` requires bearer.
  - `compress` default is `true` when omitted.
  - Raw HTML > 100KB returns validation error.
  - Success returns stateless URL with `d` and `s`, plus `url_bytes`.

**Step 2: Run test to verify it fails**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_generate.py`
- Expected: FAIL.

**Step 3: Write minimal implementation**
- Add request schema for agent-generate with `compress: bool = True`.
- Reuse current payload pipeline (`minify_html`, `compress_payload`, `sign_data`).
- Add size guard by byte count of raw HTML (`len(html.encode("utf-8")) <= 102400`).

**Step 4: Run tests to verify they pass**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_generate.py`
- Expected: PASS.

**Step 5: Commit**
```bash
git add tests/test_agent_generate.py app/interface/routes.py app/interface/schemas.py
git commit -m "feat: add bearer-protected default agent stateless generate api"
```

### Task 6: Add failing tests for optional persistent agent pages (auto slug + public route)

**Files:**
- Create: `tests/test_agent_persistent.py`
- Modify: `app/interface/routes.py`
- Modify: `app/db.py`

**Step 1: Write the failing tests**
- `POST /api/agent/apps` (Bearer):
  - With no slug -> server generates 8-char `[a-z0-9]` slug.
  - With slug -> stores user-provided slug.
  - Input >100KB raw rejected.
  - Response includes `slug` and public `url`.
- `GET /api/agent/apps` lists agent-owned pages only.
- `DELETE /api/agent/apps/{slug}` deletes only agent-owned page.
- `GET /a/{agent_id}/{slug}` serves HTML.

**Step 2: Run test to verify it fails**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_persistent.py`
- Expected: FAIL.

**Step 3: Write minimal implementation**
- Implement CRUD endpoints for agent apps with bearer auth.
- Add slug generator with collision retry.
- Add public route `GET /a/{agent_id}/{slug}`.
- Update `last_accessed_at` only in this public GET route.

**Step 4: Run tests to verify they pass**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_persistent.py`
- Expected: PASS.

**Step 5: Commit**
```bash
git add tests/test_agent_persistent.py app/interface/routes.py app/db.py
git commit -m "feat: add optional persistent agent pages with auto slug"
```

### Task 7: Add failing tests for configurable TTL and expiry cleanup behavior

**Files:**
- Create: `tests/test_agent_ttl.py`
- Modify: `app/main.py`
- Modify: `app/interface/routes.py`
- Modify: `app/db.py`

**Step 1: Write the failing tests**
- Add tests for `AGENT_APP_TTL_DAYS` behavior:
  - Default is 7.
  - Custom env value is respected.
  - Expired pages return 404 on public route.
  - Only successful public open extends `last_accessed_at`.

**Step 2: Run test to verify it fails**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_ttl.py`
- Expected: FAIL.

**Step 3: Write minimal implementation**
- Read `AGENT_APP_TTL_DAYS` in `app/main.py` and pass into route registration.
- Add expiry check helper (`is_expired(last_accessed_at, ttl_days)`).
- Keep legacy routes behavior unchanged.

**Step 4: Run tests to verify they pass**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_ttl.py`
- Expected: PASS.

**Step 5: Commit**
```bash
git add tests/test_agent_ttl.py app/main.py app/interface/routes.py app/db.py
git commit -m "feat: add configurable ttl for agent persistent pages"
```

### Task 8: Implement registration scripts (Python + Node) and validate docs alignment

**Files:**
- Modify: `scripts/register_agent.py`
- Modify: `scripts/register_agent.mjs`
- Modify: `app/public/skill.md`
- Modify: `app/public/llm.txt`
- Create: `tests/test_agent_scripts_docs.py`

**Step 1: Write the failing tests**
- Validate docs mention:
  - default `/api/agent/generate`
  - optional `/api/agent/apps`
  - 100KB limit
  - `compress` default `true`
  - TTL from last open
- Validate scripts contain:
  - challenge loop
  - register call
  - bearer output

**Step 2: Run test to verify it fails**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_scripts_docs.py`
- Expected: FAIL.

**Step 3: Write minimal implementation**
- Complete both scripts with same flow:
  - generate candidate secret
  - compute agent_id base32
  - loop until challenge passes
  - register -> receive bearer token
  - print ready-to-run API examples
- Keep dependencies minimal (`stdlib` in Python, built-in Node APIs in `.mjs`).

**Step 4: Run tests to verify they pass**
- Run: `uv run --with pytest --with python-fasthtml --with fastapi --with python-multipart pytest -q tests/test_agent_scripts_docs.py`
- Expected: PASS.

**Step 5: Commit**
```bash
git add scripts/register_agent.py scripts/register_agent.mjs app/public/skill.md app/public/llm.txt tests/test_agent_scripts_docs.py
git commit -m "feat: add agent registration scripts and aligned onboarding docs"
```

### Task 9: Final integration verification and handoff

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/conventions.md`
- Optional: `adr/2026-02-23-agent-first-home-and-api.md`

**Step 1: Update docs minimally**
- Document new agent-first flow, new endpoints, env var, limits.
- Explicitly state old keys/routes are preserved.

**Step 2: Run full quality gate**
- Run: `just check`
- Expected: PASS (known non-blocking warnings can remain if already accepted by repo policy).

**Step 3: Manual smoke checks**
- Open `/` and verify two blocks + no admin link mention.
- Download `skill.md`, `llm.txt`, both scripts.
- Run one registration script and create one stateless URL + one persistent URL.

**Step 4: Prepare final commit**
```bash
git add README.md docs/architecture.md docs/conventions.md adr/2026-02-23-agent-first-home-and-api.md
git commit -m "docs: finalize agent-first flow and compatibility guarantees"
```

**Step 5: Completion report**
- Summarize endpoints, migration safety, TTL behavior, and verification outputs.
- Request explicit user approval before any extra behavior beyond this plan.

---

## Execution Notes
- Follow @superpowers:test-driven-development for each behavior change.
- Follow @superpowers:verification-before-completion before claiming success.
- Keep commits frequent and scoped to one task.
- Do not add any new text/limits/behavior beyond agreed requirements without explicit `+` from user.

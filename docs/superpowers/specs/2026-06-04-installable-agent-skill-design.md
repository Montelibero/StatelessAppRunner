# Installable Agent Skill (agentskills.io format) — Design

Date: 2026-06-04
Status: Approved (pending spec review)

## Problem

The site (`mtlminiapps.us`) currently exposes its agent onboarding as a single
hosted markdown file `app/public/skill.md`, served at `GET /skill.md`, with the
homepage telling humans to "share this URL with your agent". This is runtime
API documentation (closer to `llm.txt`), not an installable skill.

The current open standard for agent skills is the **agentskills.io** format
(originally from Anthropic, now an open standard adopted by Claude Code, Cursor,
Codex, Gemini CLI, Copilot, and ~40 other clients). A skill in that format is a
**folder** containing a `SKILL.md` file with YAML frontmatter (`name`,
`description`) plus optional `scripts/`, `references/`, `assets/`.

We want to publish a proper installable skill in the agentskills.io format,
without breaking the existing runtime-docs approach.

## Goals

- Publish an installable skill folder in agentskills.io format.
- Keep a single source of truth for the skill text (no diverging copies).
- Keep a single source of truth for the registration scripts.
- Deliver via universal per-file URLs **and** a convenience zip.
- Do not break existing URLs (`/skill.md`, `/scripts/register_agent.*`, `/llm.txt`).
- Minimal homepage update to point users at installation.

## Non-Goals (YAGNI)

- No separate git repo / marketplace.
- No `curl | bash` auto-installer.
- No changes to API / registration logic — packaging and serving only.

## Decisions (from brainstorming)

- **Delivery:** per-file URLs + zip (covers humans, shell-capable agents, and
  agents without a shell).
- **Content source of truth:** `SKILL.md` is the single source; legacy
  `/skill.md` serves the same file.
- **Scripts source of truth:** move `register_agent.py` / `register_agent.mjs`
  into the skill folder; legacy `/scripts/register_agent.*` routes read from
  there (confirmed by user).

## Design

### 1. Skill folder layout (source of truth in repo)

```
app/public/skill/
├── SKILL.md                    # single source: YAML frontmatter + instructions
├── scripts/
│   ├── register_agent.py       # moved from repo-root scripts/
│   └── register_agent.mjs
└── references/
    └── llm.txt                 # moved from app/public/llm.txt
```

`SKILL.md` = current `skill.md` body + YAML frontmatter prepended:

```yaml
---
name: stateless-app-runner
description: Publish agent-created HTML pages as shareable links via mtlminiapps.us — stateless (HTML-in-URL) or persistent. Use when an agent needs to turn HTML into a public URL.
---
```

Body keeps the existing sections (Registration, Default mode, Optional
persistent mode, Rate limits, Retention). Script references in the body point to
local `scripts/register_agent.*` for the installed-skill case, while keeping the
absolute `https://mtlminiapps.us/scripts/...` URLs as a fallback.

Old files removed after move: `app/public/skill.md`, `app/public/llm.txt`, and
the scripts under repo-root `scripts/` (use `gio trash`, confirm before deleting
per user rules). The route's `_read_registration_script` currently probes
`app_dir/scripts` and `repo_dir/scripts`; it will be updated to read from
`app/public/skill/scripts/`.

### 2. Serving (per-file URLs + zip)

New routes in `app/interface/routes.py`, alongside existing ones, all reading
from `app/public/skill/`:

- `GET /skill/SKILL.md` → `PlainTextResponse` of `SKILL.md`.
- `GET /skill/scripts/register_agent.py` → script (text/plain).
- `GET /skill/scripts/register_agent.mjs` → script (text/plain).
- `GET /skill/references/llm.txt` → reference (text/plain).
- `GET /skill.zip` → zip of the whole `app/public/skill/` folder, generated
  in-memory (`zipfile` + `io.BytesIO`), `media_type="application/zip"`, with a
  `Content-Disposition: attachment; filename="stateless-app-runner-skill.zip"`
  header. No committed artifact — the zip always matches the on-disk files.

Backward compatibility (legacy routes now read from the new single sources):

- `GET /skill.md` → reads `app/public/skill/SKILL.md` (same file, frontmatter
  included; harmless for runtime fetch).
- `GET /scripts/register_agent.py` / `.mjs` → read from
  `app/public/skill/scripts/` (update `_read_registration_script` candidates).
- `GET /llm.txt` → reads `app/public/skill/references/llm.txt`.

### 3. Homepage update (`app/ui/pages.py`)

In the "Agent setup" / "Docs for agents" area, add a short install section:

- "Install as a skill" with the path convention for common clients (e.g. Claude
  Code: place under `~/.claude/skills/stateless-app-runner/`) and a link to
  `/skill.zip`.
- Keep the existing "share https://mtlminiapps.us/skill.md" line as a fallback
  for agents that fetch at runtime.

Scope: a few `P`/`A` elements; no page restructuring.

### 4. Tests (TDD)

Add to `tests/` (near `test_agent_onboarding_assets.py`):

- `GET /skill/SKILL.md` → 200, body starts with `---`, contains `name:` and
  `description:`.
- `GET /skill.zip` → 200, `application/zip`; archive contains `SKILL.md` and
  `scripts/register_agent.py`.
- `GET /skill/scripts/register_agent.py` → 200, non-empty.
- Regression: legacy `/skill.md`, `/scripts/register_agent.py`,
  `/scripts/register_agent.mjs`, `/llm.txt` still return 200 and non-empty.
- Consistency: body of `/scripts/register_agent.py` == body of
  `/skill/scripts/register_agent.py` (single source).

## Risks / Notes

- Moving `scripts/` may affect other references (Justfile, docs, the register
  scripts being imported in tests). Implementation must grep for existing
  references and update them.
- Frontmatter in `/skill.md` is a behavior change for runtime fetchers, but YAML
  frontmatter is inert prose for an LLM reading the file; acceptable.

# AGENTS.md

## Purpose
This repository follows an AI-first workflow: agents may implement changes autonomously, but must preserve behavior, keep changes verifiable, and leave clear project artifacts.

## Current Architecture
- ASGI core: `FastAPI` (`app/main.py`).
- System UI rendering: native `FastHTML` components (`app/ui/pages.py`).
- Storage: SQLite (`app/db.py`).
- Tests: `tests/`, `tests_db/`.

## Contract Invariants
- Keep existing public routes backward compatible unless explicitly versioned.
  - `/`, `/admin`, `/p/{slug}`, `/p{user_id}/{slug}`, `/api/*`
- Keep API payload shape and status codes stable.
- Keep path-aware security headers behavior unchanged.

## Required Workflow For Non-trivial Changes
1. Create/update an execution plan in `docs/plans/` or `docs/exec-plans/active/`.
2. Use TDD for behavior changes/bug fixes (test fails first, then pass).
3. Run full gate before completion: `just check`.
4. Update docs when architecture/contracts/workflow change.

## Quality Gates
Use `Justfile` as the single entry point:
- `just fmt`
- `just lint`
- `just typecheck`
- `just test`
- `just check` (required before claiming completion)

## Boundaries
- Prefer minimal diffs.
- Do not silently change contracts.
- Do not bypass failing checks by removing tests or guards.
- New dependency or architecture shift should be documented in `adr/`.

## Source Of Truth Docs
- `docs/architecture.md`
- `docs/conventions.md`
- `docs/glossary.md`
- `docs/quality-grades.md`
- `adr/README.md`

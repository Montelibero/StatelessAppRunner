# 2026-02-23 Main Decomposition

## Context
`app/main.py` contains routing, payload processing, and auth orchestration in a single module.

## Plan
1. [x] Create `application` layer modules for payload and auth helpers.
2. [x] Create `interface` layer modules for API schemas and route registration.
3. [x] Keep route contracts and behavior unchanged.
4. [x] Run `just check` and verify green.
5. [x] Update architecture docs if needed.

## Risks
- Route behavior drift while moving code.
- Import path issues in tests (`from main import ...`).

## Verification
- `just check`

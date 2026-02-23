# ADR: Layered Main Decomposition

## Context
`app/main.py` accumulated routing, payload logic, auth checks, and app wiring in one file.

## Decision
Refactor to layered structure:
- composition root in `app/main.py`
- interface in `app/interface/*`
- application logic in `app/application/*`
- infrastructure in `app/db.py`

## Consequences
- Clearer ownership and lower change risk.
- Better alignment with AI-first architecture constraints.
- Existing public routes remain backward-compatible.

## Alternatives Considered
- Keep single-file `main.py`: rejected due to maintainability and agent-context burden.

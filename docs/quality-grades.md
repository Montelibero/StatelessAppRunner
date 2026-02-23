# Quality Grades

## Snapshot (2026-02-23)

- Composition + Interface (`app/main.py`, `app/interface/*`): **A-**
  - Strengths: layered split, stable contracts, route logic isolated from app wiring.
  - Debt: further modularization of route handlers can reduce file size in `routes.py`.

- Application (`app/application/*`): **A-**
  - Strengths: payload/auth logic extracted, reusable helpers, cleaner testability.
  - Debt: could add dedicated unit tests for each helper module.

- Infrastructure (`app/db.py`): **B+**
  - Strengths: migration handling, user isolation, connection-path resilience.
  - Debt: still a large module; could be split into repository + migration helpers.

- UI rendering (`app/ui/pages.py`): **B+**
  - Strengths: native FastHTML rendering, no template file dependency.
  - Debt: large inline admin JS block; can be modularized.

- Quality guardrails (`Justfile`, `.linters/arch_test.py`, CI): **A**
  - Strengths: one-command gate (`just check`), structural layer checks, CI enforcement.
  - Debt: arch checks can evolve to full import-graph cycle checks.

## Next Improvements

1. Split `app/interface/routes.py` into smaller API-focused modules.
2. Add unit tests for `app/application/payload.py` and `app/application/auth.py`.
3. Expand `.linters/arch_test.py` to detect import cycles and forbidden transitive dependencies.

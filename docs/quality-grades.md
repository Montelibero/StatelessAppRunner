# Quality Grades

## Snapshot (2026-02-23)

- Interface/API (`app/main.py`): **B**
  - Strengths: strong integration tests, stable API behavior.
  - Debt: large file, mixed concerns.
- Database (`app/db.py`): **B**
  - Strengths: migration handling, user isolation, test coverage.
  - Debt: deprecated datetime usage warnings.
- UI rendering (`app/ui/pages.py`): **B-**
  - Strengths: FastHTML integration without route contract changes.
  - Debt: transitional approach still depends on legacy templates as source markup.
- Test suite (`tests/`, `tests_db/`): **B+**
  - Strengths: broad behavior coverage, migration and security header tests.
  - Debt: warning cleanup pending.

## Next Improvements

1. Replace deprecated `datetime.utcnow()` with timezone-aware UTC.
2. Split `app/main.py` into smaller modules.
3. Move from template-backed FastHTML rendering to native component composition.

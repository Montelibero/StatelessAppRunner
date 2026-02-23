set shell := ["bash", "-euo", "pipefail", "-c"]

default:
  @just --list

fmt:
  uv run --with ruff ruff check --fix .
  uv run --with ruff ruff format .

lint:
  uv run --with ruff ruff check .
  uv run --with ruff ruff format --check .

typecheck:
  uv run --with pyright --with pytest --with python-fasthtml --with fastapi --with python-multipart pyright

test-fast:
  uv run --with pytest --with python-fasthtml pytest tests tests_db -q

test:
  uv run --with pytest --with python-fasthtml --with pytest-cov pytest -q --cov=app --cov-report=term --cov-fail-under=85

docs-check:
  test -f docs/architecture.md
  test -f docs/conventions.md
  test -f docs/golden-principles.md
  test -f docs/glossary.md
  test -f docs/quality-grades.md
  test -d docs/runbooks
  test -f docs/runbooks/README.md
  test -f docs/runbooks/docker-deploy-and-rollback.md
  test -f docs/runbooks/ci-quality-gate-failure.md
  test -d docs/exec-plans/active
  test -f adr/README.md
  test -f adr/2026-02-23-fasthtml-ui-migration.md
  test -f adr/2026-02-23-layered-main-decomposition.md
  test -f adr/2026-02-23-quality-gates-and-ci.md

arch-test:
  uv run --with python-fasthtml python .linters/arch_test.py

metrics:
  @echo "Python files: $$(rg --files app tests tests_db | wc -l)"
  @echo "Tests: $$(rg -n '^def test_' tests tests_db | wc -l)"

check: docs-check arch-test lint typecheck test

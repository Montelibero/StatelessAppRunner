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
  uv run --with pyright --with python-fasthtml --with fastapi --with python-multipart pyright

test-fast:
  uv run --with python-fasthtml pytest tests tests_db -q

test:
  uv run --with python-fasthtml pytest -q

docs-check:
  test -f docs/architecture.md
  test -f docs/conventions.md
  test -f docs/glossary.md
  test -f docs/quality-grades.md
  test -d docs/exec-plans/active
  test -f adr/README.md

arch-test:
  uv run --with python-fasthtml python -c "import pathlib; p=pathlib.Path('app/main.py'); s=p.read_text(encoding='utf-8'); assert 'from ui.pages import' in s, 'main.py must render system UI via ui.pages'; print('arch-test: ok')"

metrics:
  @echo "Python files: $$(rg --files app tests tests_db | wc -l)"
  @echo "Tests: $$(rg -n '^def test_' tests tests_db | wc -l)"

check: docs-check arch-test lint typecheck test

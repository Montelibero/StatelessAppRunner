# FastHTML + AI-First Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate UI rendering to FastHTML while keeping all existing routes/contracts unchanged, and add AI-first project scaffolding.

**Architecture:** Keep FastAPI as the ASGI core and existing API/router behavior unchanged. Introduce a dedicated `app/ui` layer that renders HTML pages via FastHTML. Add minimal AI-first docs and execution-plan structure to guide future iterations.

**Tech Stack:** FastAPI, python-fasthtml, pytest, sqlite

---

### Task 1: Add failing tests for new UI rendering layer

**Files:**
- Create: `tests/test_ui_pages.py`
- Modify: `tests/test_main.py`

**Step 1: Write failing test**
- Add tests importing `app.ui.pages` and asserting rendered HTML for home/admin contains required markers.

**Step 2: Run test to verify it fails**
- Run: `uv run pytest tests/test_ui_pages.py -q`
- Expected: FAIL (module missing)

**Step 3: Write minimal implementation**
- Create `app/ui/pages.py` with FastHTML-based render functions.

**Step 4: Run tests to verify pass**
- Run: `uv run pytest tests/test_ui_pages.py -q`

**Step 5: Commit**
- `git add tests/test_ui_pages.py app/ui/pages.py`
- `git commit -m "feat: add FastHTML UI rendering module"`

### Task 2: Wire FastHTML pages into existing routes

**Files:**
- Modify: `app/main.py`
- Modify: `app/requirements.txt`

**Step 1: Write failing integration test**
- Assert `/` and `/admin` still return expected content after removing Jinja dependency.

**Step 2: Run failing test**
- `uv run pytest tests/test_main.py::test_admin_page tests/test_homepage.py::test_homepage_structure -q`

**Step 3: Implement minimal wiring**
- Replace template-based route rendering with `app.ui.pages` output.
- Keep all routes and response formats unchanged.

**Step 4: Verify green**
- `uv run pytest tests/test_main.py::test_admin_page tests/test_homepage.py::test_homepage_structure -q`

**Step 5: Commit**
- `git add app/main.py app/requirements.txt`
- `git commit -m "refactor: serve home/admin via FastHTML"`

### Task 3: Add AI-first repository scaffolding

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/conventions.md`
- Create: `docs/glossary.md`
- Create: `docs/quality-grades.md`
- Create: `docs/exec-plans/active/README.md`
- Create: `adr/README.md`

**Step 1: Write failing docs test/check (if present) or checklist**
- Ensure required docs exist and are linked.

**Step 2: Implement minimal docs**
- Add concise, repo-specific content (not boilerplate).

**Step 3: Verify**
- Run: `uv run pytest -q`

**Step 4: Commit**
- `git add docs adr`
- `git commit -m "docs: add AI-first project scaffolding"`

### Task 4: Final verification and handoff

**Files:**
- Modify: `README.md` (if needed)

**Step 1:** Run full verification
- `uv run pytest -q`

**Step 2:** Summarize compatibility guarantees
- Confirm unchanged routes and payload contracts.

**Step 3:** Final commit
- `git add -A`
- `git commit -m "chore: complete phase-1 FastHTML + AI-first migration"`

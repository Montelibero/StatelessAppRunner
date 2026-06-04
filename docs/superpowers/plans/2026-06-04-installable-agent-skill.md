# Installable Agent Skill (agentskills.io format) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the service's agent onboarding as an installable skill in the agentskills.io format (a `SKILL.md` folder), served via per-file URLs and a zip, without breaking existing endpoints.

**Architecture:** Consolidate the skill text, the registration scripts, and `llm.txt` into a single canonical folder `app/public/skill/`. Legacy routes (`/skill.md`, `/llm.txt`, `/scripts/register_agent.*`) keep working by reading from the new folder (single source of truth). New routes expose the skill folder per-file (`/skill/...`) and as an on-the-fly zip (`/skill.zip`).

**Tech Stack:** Python, FastAPI, `fastapi.responses` (PlainTextResponse, Response), stdlib `zipfile` + `io.BytesIO`, pytest + `fastapi.testclient`.

---

## File Structure

- `app/public/skill/SKILL.md` — created: YAML frontmatter + existing skill body (single source of skill text).
- `app/public/skill/scripts/register_agent.py` — moved from `scripts/register_agent.py`.
- `app/public/skill/scripts/register_agent.mjs` — moved from `scripts/register_agent.mjs`.
- `app/public/skill/references/llm.txt` — moved from `app/public/llm.txt`.
- `app/interface/routes.py` — modified: repoint legacy routes to the new folder; add `/skill/...` and `/skill.zip` routes.
- `app/ui/pages.py` — modified: add a short "Install as a skill" block.
- `tests/test_agent_scripts_docs.py` — modified: update filesystem paths.
- `tests/test_openapi.py` — modified: add new routes to the schema-excluded set.
- `tests/test_skill_package.py` — created: tests for new `/skill/...` and `/skill.zip` routes.
- `tests/test_homepage.py` / `tests/test_ui_pages.py` — modified: assert the new install block.

Files removed (via `gio trash`, after `git mv` where applicable): old `app/public/skill.md`, `app/public/llm.txt`, `scripts/register_agent.py`, `scripts/register_agent.mjs`.

---

### Task 1: Move registration scripts into the skill folder

**Files:**
- Move: `scripts/register_agent.py` → `app/public/skill/scripts/register_agent.py`
- Move: `scripts/register_agent.mjs` → `app/public/skill/scripts/register_agent.mjs`
- Modify: `app/interface/routes.py:213-221` (`_read_registration_script`)
- Modify: `tests/test_agent_scripts_docs.py:53,63`

- [ ] **Step 1: Update the filesystem-path tests to the new location (failing)**

In `tests/test_agent_scripts_docs.py`, change the two paths:

```python
    text = Path("app/public/skill/scripts/register_agent.py").read_text(encoding="utf-8")
```
```python
    text = Path("app/public/skill/scripts/register_agent.mjs").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `just pytest tests/test_agent_scripts_docs.py -q`
Expected: FAIL — `FileNotFoundError` for the new paths.

- [ ] **Step 3: Move the script files (preserving git history)**

```bash
mkdir -p app/public/skill/scripts
git mv scripts/register_agent.py app/public/skill/scripts/register_agent.py
git mv scripts/register_agent.mjs app/public/skill/scripts/register_agent.mjs
```

- [ ] **Step 4: Repoint `_read_registration_script` to the new folder**

In `app/interface/routes.py`, replace the `candidates` tuple (currently lines 214-217):

```python
    def _read_registration_script(filename: str) -> str:
        candidates = (
            app_dir / "public" / "skill" / "scripts" / filename,
        )
        for path in candidates:
            if path.exists():
                return path.read_text(encoding="utf-8")
        raise HTTPException(status_code=404, detail=f"{filename} not found")
```

- [ ] **Step 5: Run the scripts-docs tests and the onboarding-assets tests**

Run: `just pytest tests/test_agent_scripts_docs.py tests/test_agent_onboarding_assets.py -q`
Expected: PASS (the legacy `/scripts/register_agent.*` routes still serve from the new path).

- [ ] **Step 6: Commit**

```bash
git add app/public/skill/scripts app/interface/routes.py tests/test_agent_scripts_docs.py
git commit -m "refactor: move registration scripts into app/public/skill/scripts"
```

---

### Task 2: Create SKILL.md (frontmatter) as the single skill source

**Files:**
- Move: `app/public/skill.md` → `app/public/skill/SKILL.md`
- Modify: `app/public/skill/SKILL.md` (prepend frontmatter)
- Modify: `app/interface/routes.py:362-369` (`skill_md` route)
- Modify: `tests/test_agent_scripts_docs.py:5`

- [ ] **Step 1: Update the skill-text filesystem test to the new path and assert frontmatter (failing)**

In `tests/test_agent_scripts_docs.py`, change line 5 and add two assertions at the top of `test_skill_md_contains_required_agent_flow`:

```python
    text = Path("app/public/skill/SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: stateless-app-runner" in text
    assert "description:" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `just pytest tests/test_agent_scripts_docs.py::test_skill_md_contains_required_agent_flow -q`
Expected: FAIL — `FileNotFoundError` for `app/public/skill/SKILL.md`.

- [ ] **Step 3: Move skill.md and prepend frontmatter**

```bash
git mv app/public/skill.md app/public/skill/SKILL.md
```

Then prepend this frontmatter block to `app/public/skill/SKILL.md` (above the existing `# Agent Skill` line, leave the rest of the body unchanged):

```markdown
---
name: stateless-app-runner
description: Publish agent-created HTML pages as shareable links via mtlminiapps.us — stateless (HTML embedded in the URL) or persistent (HTML stored on the server). Use when an agent needs to turn HTML into a public URL.
---

```

- [ ] **Step 4: Repoint the `/skill.md` route to the new file**

In `app/interface/routes.py`, update the `skill_md` route body:

```python
    @app.get("/skill.md", response_class=PlainTextResponse, include_in_schema=False)
    async def skill_md():
        path = app_dir / "public" / "skill" / "SKILL.md"
        if not path.exists():
            raise HTTPException(status_code=404, detail="skill.md not found")
        return PlainTextResponse(
            path.read_text(encoding="utf-8"), media_type="text/markdown"
        )
```

- [ ] **Step 5: Run the scripts-docs and onboarding-assets tests**

Run: `just pytest tests/test_agent_scripts_docs.py tests/test_agent_onboarding_assets.py -q`
Expected: PASS (`/skill.md` still returns the body with the required strings, now plus frontmatter).

- [ ] **Step 6: Commit**

```bash
git add app/public/skill/SKILL.md app/interface/routes.py tests/test_agent_scripts_docs.py
git commit -m "feat: add SKILL.md frontmatter and serve it as the single skill source"
```

---

### Task 3: Move llm.txt into the skill references folder

**Files:**
- Move: `app/public/llm.txt` → `app/public/skill/references/llm.txt`
- Modify: `app/interface/routes.py:371-378` (`llm_txt` route)
- Modify: `tests/test_agent_scripts_docs.py:31`

- [ ] **Step 1: Update the llm.txt filesystem test path (failing)**

In `tests/test_agent_scripts_docs.py`, change line 31:

```python
    text = Path("app/public/skill/references/llm.txt").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `just pytest tests/test_agent_scripts_docs.py::test_llm_txt_contains_required_agent_flow -q`
Expected: FAIL — `FileNotFoundError`.

- [ ] **Step 3: Move the file**

```bash
mkdir -p app/public/skill/references
git mv app/public/llm.txt app/public/skill/references/llm.txt
```

- [ ] **Step 4: Repoint the `/llm.txt` route**

In `app/interface/routes.py`, update the `llm_txt` route body:

```python
    @app.get("/llm.txt", response_class=PlainTextResponse, include_in_schema=False)
    async def llm_txt():
        path = app_dir / "public" / "skill" / "references" / "llm.txt"
        if not path.exists():
            raise HTTPException(status_code=404, detail="llm.txt not found")
        return PlainTextResponse(
            path.read_text(encoding="utf-8"), media_type="text/plain"
        )
```

- [ ] **Step 5: Run the scripts-docs and onboarding-assets tests**

Run: `just pytest tests/test_agent_scripts_docs.py tests/test_agent_onboarding_assets.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/public/skill/references/llm.txt app/interface/routes.py tests/test_agent_scripts_docs.py
git commit -m "refactor: move llm.txt into app/public/skill/references"
```

---

### Task 4: Add per-file `/skill/...` routes

**Files:**
- Modify: `app/interface/routes.py` (add routes after the `register_agent_mjs` route, ~line 621)
- Test: `tests/test_skill_package.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_skill_package.py`:

```python
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_skill_md_folder_route_has_frontmatter():
    response = client.get("/skill/SKILL.md")
    assert response.status_code == 200
    assert response.text.startswith("---\n")
    assert "name: stateless-app-runner" in response.text
    assert "description:" in response.text


def test_skill_scripts_routes_available():
    py = client.get("/skill/scripts/register_agent.py")
    mjs = client.get("/skill/scripts/register_agent.mjs")
    assert py.status_code == 200
    assert mjs.status_code == 200
    assert "python" in py.text.lower()
    assert "node" in mjs.text.lower() or "mjs" in mjs.text.lower()


def test_skill_references_llm_txt_available():
    response = client.get("/skill/references/llm.txt")
    assert response.status_code == 200
    assert "POST https://mtlminiapps.us/api/agent/generate" in response.text


def test_skill_folder_script_matches_legacy_route():
    legacy = client.get("/scripts/register_agent.py")
    packaged = client.get("/skill/scripts/register_agent.py")
    assert legacy.status_code == 200 and packaged.status_code == 200
    assert legacy.text == packaged.text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `just pytest tests/test_skill_package.py -q`
Expected: FAIL — the `/skill/...` routes return 404.

- [ ] **Step 3: Add the routes**

In `app/interface/routes.py`, immediately after the `register_agent_mjs` route (around line 621), add:

```python
    @app.get(
        "/skill/SKILL.md", response_class=PlainTextResponse, include_in_schema=False
    )
    async def skill_package_md():
        path = app_dir / "public" / "skill" / "SKILL.md"
        if not path.exists():
            raise HTTPException(status_code=404, detail="SKILL.md not found")
        return PlainTextResponse(
            path.read_text(encoding="utf-8"), media_type="text/markdown"
        )

    @app.get(
        "/skill/scripts/register_agent.py",
        response_class=PlainTextResponse,
        include_in_schema=False,
    )
    async def skill_package_register_py():
        return PlainTextResponse(
            _read_registration_script("register_agent.py"),
            media_type="text/plain",
        )

    @app.get(
        "/skill/scripts/register_agent.mjs",
        response_class=PlainTextResponse,
        include_in_schema=False,
    )
    async def skill_package_register_mjs():
        return PlainTextResponse(
            _read_registration_script("register_agent.mjs"),
            media_type="text/plain",
        )

    @app.get(
        "/skill/references/llm.txt",
        response_class=PlainTextResponse,
        include_in_schema=False,
    )
    async def skill_package_llm_txt():
        path = app_dir / "public" / "skill" / "references" / "llm.txt"
        if not path.exists():
            raise HTTPException(status_code=404, detail="llm.txt not found")
        return PlainTextResponse(
            path.read_text(encoding="utf-8"), media_type="text/plain"
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `just pytest tests/test_skill_package.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/interface/routes.py tests/test_skill_package.py
git commit -m "feat: serve skill folder files at /skill/* routes"
```

---

### Task 5: Add the `/skill.zip` route (in-memory zip)

**Files:**
- Modify: `app/interface/routes.py:16` (import `Response`) and add the zip route
- Modify: `tests/test_skill_package.py` (add zip tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_skill_package.py`:

```python
import io
import zipfile


def test_skill_zip_downloads():
    response = client.get("/skill.zip")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers.get("content-disposition", "")


def test_skill_zip_contains_skill_files():
    response = client.get("/skill.zip")
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    names = set(archive.namelist())
    assert "SKILL.md" in names
    assert "scripts/register_agent.py" in names
    assert "scripts/register_agent.mjs" in names
    assert "references/llm.txt" in names
    assert archive.read("SKILL.md").decode("utf-8").startswith("---\n")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `just pytest tests/test_skill_package.py -k zip -q`
Expected: FAIL — `/skill.zip` returns 404.

- [ ] **Step 3: Import `Response` and add the zip route**

In `app/interface/routes.py`, update the responses import (line 16) to include `Response`:

```python
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
```

Then add this route right after the `/skill/references/llm.txt` route from Task 4:

```python
    @app.get("/skill.zip", include_in_schema=False)
    async def skill_zip():
        skill_root = app_dir / "public" / "skill"
        if not skill_root.exists():
            raise HTTPException(status_code=404, detail="skill folder not found")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for file_path in sorted(skill_root.rglob("*")):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(skill_root).as_posix())
        buffer.seek(0)
        return Response(
            content=buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": (
                    'attachment; filename="stateless-app-runner-skill.zip"'
                )
            },
        )
```

Add the stdlib imports near the top of `app/interface/routes.py` (after the existing `import json` on line 10):

```python
import io
import zipfile
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `just pytest tests/test_skill_package.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/interface/routes.py tests/test_skill_package.py
git commit -m "feat: serve installable skill as /skill.zip"
```

---

### Task 6: Keep new routes out of the OpenAPI schema

**Files:**
- Modify: `tests/test_openapi.py:14-33` (forbidden set)

- [ ] **Step 1: Add the new routes to the forbidden set (regression test)**

In `tests/test_openapi.py`, add these entries to the `forbidden` set:

```python
        "/skill/SKILL.md",
        "/skill/scripts/register_agent.py",
        "/skill/scripts/register_agent.mjs",
        "/skill/references/llm.txt",
        "/skill.zip",
```

- [ ] **Step 2: Run the test to verify it passes**

Run: `just pytest tests/test_openapi.py -q`
Expected: PASS (all new routes use `include_in_schema=False`, so they never appear in `paths`).

- [ ] **Step 3: Commit**

```bash
git add tests/test_openapi.py
git commit -m "test: assert skill package routes stay out of openapi schema"
```

---

### Task 7: Add "Install as a skill" block to the homepage

**Files:**
- Modify: `app/ui/pages.py` (inside the `id="llm"` block, after line 336)
- Modify: `tests/test_homepage.py` (add assertions)
- Modify: `tests/test_ui_pages.py` (add assertions)

- [ ] **Step 1: Write the failing homepage assertions**

In `tests/test_homepage.py`, inside `test_homepage_structure`, add after line 66:

```python
    assert "Install as a skill" in response.text
    assert "~/.claude/skills/stateless-app-runner/" in response.text
    assert 'href="/skill.zip"' in response.text
```

In `tests/test_ui_pages.py`, add a matching assertion in the page-content test (after the existing skill assertions):

```python
    assert "Install as a skill" in html
    assert 'href="/skill.zip"' in html
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just pytest tests/test_homepage.py tests/test_ui_pages.py -q`
Expected: FAIL — the new strings are not present.

- [ ] **Step 3: Add the install block to the page**

In `app/ui/pages.py`, inside the `Div(..., id="llm", cls="mb-2")` block, immediately after the human-fallback `P(...)` that ends on line 338, insert:

```python
                                    P(
                                        "Install as a skill",
                                        cls="has-text-weight-semibold mt-3 mb-1",
                                    ),
                                    P(
                                        NotStr(
                                            'Agentskills.io format. Download '
                                            '<a href="/skill.zip">/skill.zip</a> '
                                            'and unpack it into your client\'s skills '
                                            'folder (e.g. Claude Code: '
                                            '<code>~/.claude/skills/stateless-app-runner/</code>).'
                                        ),
                                        cls="is-size-7 has-text-grey",
                                    ),
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just pytest tests/test_homepage.py tests/test_ui_pages.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/ui/pages.py tests/test_homepage.py tests/test_ui_pages.py
git commit -m "feat: add install-as-a-skill block to homepage"
```

---

### Task 8: Full suite + cleanup verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `just test` (or `just pytest -q`)
Expected: PASS, no failures.

- [ ] **Step 2: Confirm no stale references to old paths remain**

Run:
```bash
grep -rn "public/skill.md\|public/llm.txt\|\"scripts/register_agent\|'scripts/register_agent" --include="*.py" app tests
```
Expected: no output (all references now point at `app/public/skill/...`). If the empty `scripts/` directory remains with only `__pycache__`, remove it:
```bash
gio trash scripts/__pycache__ 2>/dev/null; rmdir scripts 2>/dev/null || true
```

- [ ] **Step 3: Run lint**

Run: `just lint` (or the project's configured ruff/pyright recipe)
Expected: clean.

- [ ] **Step 4: Commit any cleanup**

```bash
git add -A
git commit -m "chore: remove stale scripts directory after skill packaging" || echo "nothing to commit"
```

---

## Notes

- Frontmatter on `/skill.md` is a behavior change for runtime fetchers but is inert prose for an LLM reading the file; the existing onboarding test only checks for required body strings, which remain.
- The zip is generated in-memory per request, so it always matches the on-disk skill folder — no committed artifact to drift.
- If `just test` / `just lint` recipe names differ, read `Justfile` first (per project rules) and use the actual recipe.

import ast
import pathlib
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def import_roots(tree: ast.AST) -> Iterable[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                yield node.module.split(".")[0]


def parse_file(path: pathlib.Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def in_dir(path: pathlib.Path, name: str) -> bool:
    try:
        path.relative_to(APP / name)
        return True
    except ValueError:
        return False


def check_file(path: pathlib.Path) -> list[str]:
    errs: list[str] = []
    tree = parse_file(path)
    roots = set(import_roots(tree))
    rel = path.relative_to(ROOT)

    if in_dir(path, "application"):
        forbidden = {"interface", "ui", "main"}
        bad = sorted(roots & forbidden)
        if bad:
            errs.append(f"{rel}: application layer must not import {', '.join(bad)}")

    if in_dir(path, "ui"):
        forbidden = {"interface", "application", "db", "main"}
        bad = sorted(roots & forbidden)
        if bad:
            errs.append(f"{rel}: ui layer must not import {', '.join(bad)}")

    if rel == pathlib.Path("app/db.py"):
        forbidden = {"interface", "ui", "main"}
        bad = sorted(roots & forbidden)
        if bad:
            errs.append(
                f"{rel}: infrastructure db layer must not import {', '.join(bad)}"
            )

    if rel == pathlib.Path("app/main.py"):
        required = {
            "from interface.routes import register_routes": "main.py must register routes via interface layer",
        }
        text = path.read_text(encoding="utf-8")
        for marker, msg in required.items():
            if marker not in text:
                errs.append(f"{rel}: {msg}")

    if rel == pathlib.Path("app/interface/routes.py"):
        text = path.read_text(encoding="utf-8")
        if "from ui.pages import" not in text:
            errs.append(
                f"{rel}: interface routes must keep system UI rendering via ui.pages"
            )

    return errs


def main() -> int:
    files = sorted((APP).rglob("*.py"))
    errors: list[str] = []
    for path in files:
        errors.extend(check_file(path))

    if errors:
        print("arch-test failed:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("arch-test: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

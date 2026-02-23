import ast
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def module_name(path: pathlib.Path) -> str:
    rel = path.relative_to(APP)
    if rel.name == "__init__.py":
        return ""
    return str(rel.with_suffix("")).replace("/", ".")


def parse_file(path: pathlib.Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def in_dir(path: pathlib.Path, name: str) -> bool:
    try:
        path.relative_to(APP / name)
        return True
    except ValueError:
        return False


def normalize_target(raw: str, modules: set[str]) -> str | None:
    if raw in modules:
        return raw

    cur = raw
    while "." in cur:
        cur = cur.rsplit(".", 1)[0]
        if cur in modules:
            return cur
    return None


def internal_imports(tree: ast.AST, modules: set[str]) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = normalize_target(alias.name, modules)
                if target:
                    out.add(target)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                target = normalize_target(node.module, modules)
                if target:
                    out.add(target)
    return out


def has_prefix(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def first_reachable_forbidden(
    graph: dict[str, set[str]], start: str, forbidden_prefixes: set[str]
) -> str | None:
    stack = [start]
    seen = {start}
    while stack:
        cur = stack.pop()
        for nxt in graph.get(cur, set()):
            if any(has_prefix(nxt, p) for p in forbidden_prefixes):
                return nxt
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return None


def detect_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    color: dict[str, int] = defaultdict(int)  # 0=white, 1=gray, 2=black
    parent: dict[str, str] = {}

    def dfs(node: str) -> list[str] | None:
        color[node] = 1
        for nxt in graph.get(node, set()):
            if color[nxt] == 0:
                parent[nxt] = node
                cycle = dfs(nxt)
                if cycle:
                    return cycle
            elif color[nxt] == 1:
                cycle = [nxt]
                cur = node
                while cur != nxt:
                    cycle.append(cur)
                    cur = parent[cur]
                cycle.append(nxt)
                cycle.reverse()
                return cycle
        color[node] = 2
        return None

    for node in sorted(graph):
        if color[node] == 0:
            cycle = dfs(node)
            if cycle:
                return cycle
    return None


def main() -> int:
    files = sorted(p for p in APP.rglob("*.py") if p.name != "__init__.py")
    modules = {module_name(p) for p in files}

    graph: dict[str, set[str]] = {}
    text_by_module: dict[str, str] = {}
    path_by_module: dict[str, pathlib.Path] = {}
    errors: list[str] = []

    for path in files:
        mod = module_name(path)
        tree = parse_file(path)
        imports = internal_imports(tree, modules)
        graph[mod] = imports
        text_by_module[mod] = path.read_text(encoding="utf-8")
        path_by_module[mod] = path

    # Required architecture markers.
    main_text = text_by_module.get("main", "")
    if "from interface.routes import register_routes" not in main_text:
        errors.append("app/main.py: main.py must register routes via interface layer")

    routes_text = text_by_module.get("interface.routes", "")
    if "from ui.pages import" not in routes_text:
        errors.append(
            "app/interface/routes.py: interface routes must keep system UI rendering via ui.pages"
        )

    # Layer constraints (transitive).
    for mod in sorted(modules):
        path = path_by_module[mod]
        rel = path.relative_to(ROOT)

        if has_prefix(mod, "application"):
            bad = first_reachable_forbidden(graph, mod, {"interface", "ui", "main"})
            if bad:
                errors.append(f"{rel}: application layer must not depend on {bad}")

        if has_prefix(mod, "ui"):
            bad = first_reachable_forbidden(
                graph, mod, {"interface", "application", "db", "main"}
            )
            if bad:
                errors.append(f"{rel}: ui layer must not depend on {bad}")

        if mod == "db":
            bad = first_reachable_forbidden(graph, mod, {"interface", "ui", "main"})
            if bad:
                errors.append(f"{rel}: db layer must not depend on {bad}")

    cycle = detect_cycle(graph)
    if cycle:
        errors.append("import cycle detected in app/: " + " -> ".join(cycle))

    if errors:
        print("arch-test failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("arch-test: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

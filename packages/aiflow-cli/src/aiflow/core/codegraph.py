from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .file_scan import list_project_files
from .markdown import now_stamp


def codegraph_dir(root: Path) -> Path:
    return root / ".aiflow" / "codegraph"


def build_codegraph(root: Path, *, output_dir: Path | None = None) -> dict[str, Any]:
    output = output_dir or codegraph_dir(root)
    output.mkdir(parents=True, exist_ok=True)
    generated_at = now_stamp()
    python_files = project_python_files(root)
    modules: list[dict[str, Any]] = []
    symbols: list[dict[str, Any]] = []
    entrypoints: list[dict[str, Any]] = []

    for relative in python_files:
        path = root / relative
        module = scan_python_module(root, path)
        modules.append(module)
        symbols.extend(module.pop("symbols"))
        for symbol in symbols:
            if symbol["path"] == relative.as_posix() and symbol["kind"] == "function" and symbol["name"] == "main":
                entrypoints.append({"id": f"{symbol['path']}:{symbol['name']}", "path": symbol["path"], "name": symbol["name"]})

    modules_payload = {"layer": "CodeGraph", "generated_at": generated_at, "modules": modules}
    symbols_payload = {"layer": "CodeGraph", "generated_at": generated_at, "symbols": symbols}
    entrypoints_payload = {"layer": "CodeGraph", "generated_at": generated_at, "entrypoints": entrypoints}
    write_json(output / "modules.json", modules_payload)
    write_json(output / "symbols.json", symbols_payload)
    write_json(output / "entrypoints.json", entrypoints_payload)
    summary = render_codegraph_summary(modules_payload, symbols_payload, entrypoints_payload)
    (output / "summary.md").write_text(summary, encoding="utf-8", newline="\n")
    return {"modules": modules_payload, "symbols": symbols_payload, "entrypoints": entrypoints_payload, "summary": summary}


def project_python_files(root: Path) -> list[Path]:
    files, _method = list_project_files(root, limit=10_000)
    return [Path(path) for path in files if path.endswith(".py")]


def scan_python_module(root: Path, path: Path) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
    except SyntaxError:
        return {"path": relative, "language": "python", "imports": [], "symbols": []}

    imports: list[str] = []
    symbols: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.append(module)
        elif isinstance(node, ast.ClassDef):
            symbols.append({"id": f"{relative}:{node.name}", "path": relative, "name": node.name, "kind": "class", "line": node.lineno})
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(
                        {
                            "id": f"{relative}:{node.name}.{child.name}",
                            "path": relative,
                            "name": child.name,
                            "kind": "method",
                            "parent": node.name,
                            "line": child.lineno,
                        }
                    )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append({"id": f"{relative}:{node.name}", "path": relative, "name": node.name, "kind": "function", "line": node.lineno})
    return {"path": relative, "language": "python", "imports": sorted(set(imports)), "symbols": symbols}


def render_codegraph_summary(modules_payload: dict[str, Any], symbols_payload: dict[str, Any], entrypoints_payload: dict[str, Any]) -> str:
    return f"""# CodeGraph

CodeGraph is the code structure layer.

- Modules: {len(modules_payload["modules"])}
- Symbols: {len(symbols_payload["symbols"])}
- Entry points: {len(entrypoints_payload["entrypoints"])}
"""


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

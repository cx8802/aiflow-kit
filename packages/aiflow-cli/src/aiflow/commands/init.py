from __future__ import annotations

from argparse import Namespace

from ..core.files import write_text_safely
from ..core.paths import ensure_aiflow_dir, project_root
from ..core.project_scan import build_context_report
from ..core.resources import read_template


def run_init(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    results: list[str] = []

    files = [(".aiflow/config.toml", "config.toml")]
    if not args.no_codex:
        files.append(("AGENTS.md", "AGENTS.md"))
    if not args.no_claude:
        files.append(("CLAUDE.md", "CLAUDE.md"))

    for relative, template in files:
        path, status = write_text_safely(root / relative, read_template(template), force=args.force)
        results.append(f"{status}: {path.relative_to(root)}")

    if not args.no_context:
        path, status = write_text_safely(root / ".aiflow" / "context.md", build_context_report(root), force=True)
        results.append(f"{status}: {path.relative_to(root)}")

    print("Initialized aiflow project files:")
    for line in results:
        print(f"- {line}")
    return 0

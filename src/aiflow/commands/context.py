from __future__ import annotations

from argparse import Namespace

from ..core.files import write_text_safely
from ..core.paths import ensure_aiflow_dir, project_root
from ..core.project_scan import build_context_report


def run_context(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    output = args.output or (root / ".aiflow" / "context.md")
    path, status = write_text_safely(output, build_context_report(root), force=True)
    print(f"{status}: {path}")
    return 0

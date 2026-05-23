from __future__ import annotations

from argparse import Namespace

from ..core.files import write_text_safely
from ..core.paths import ensure_aiflow_dir, project_root
from ..core.resources import read_template


def run_plan(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    goal = " ".join(args.goal).strip() or "<describe goal>"
    content = read_template("plan.md").replace("{{ goal }}", goal)
    path, status = write_text_safely(root / ".aiflow" / "plan.md", content, force=args.force)
    print(f"{status}: {path.relative_to(root)}")
    return 0

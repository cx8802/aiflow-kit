from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import Any

from ..core.config import load_config
from ..core.files import write_text_safely
from ..core.git import git_available, git_lines, run_git
from ..core.markdown import bullet, now_stamp
from ..core.paths import ensure_aiflow_dir, project_root
from ..core.risk_rules import risk_signals


def run_review(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    output = args.output or (root / ".aiflow" / "review.md")
    result = run_review_report(root, output)
    print(f"{result['status_text']}: {result['path']}")
    return 0


def run_review_report(root: Path, output: Path) -> dict[str, Any]:
    output_path = output if output.suffix else output / "review.md"
    output_dir = output_path.parent
    config = load_config(root)

    if not git_available(root):
        changed_files: list[str] = []
        diff_stat = ["Git repository not detected."]
        status = ["Git repository not detected."]
    else:
        changed_files = git_lines(root, ["diff", "--name-only"])
        staged = git_lines(root, ["diff", "--cached", "--name-only"])
        changed_files = sorted(set(changed_files + staged))
        diff = run_git(root, ["diff", "--stat"])
        cached_diff = run_git(root, ["diff", "--cached", "--stat"])
        diff_stat = [line for line in (diff.stdout + cached_diff.stdout).splitlines() if line.strip()] or ["No diff."]
        status = git_lines(root, ["status", "--short"]) or ["Working tree clean."]

    risks = risk_signals(changed_files, config.get("review", {}).get("high_risk_paths", []))
    report = f"""# Review Input

## Generated At

{now_stamp()}

## Git Status

{bullet(status)}
## Changed Files

{bullet([f"`{path}`" for path in changed_files])}
## Diff Summary

{bullet(diff_stat)}
## High Risk Signals

{bullet(risks)}
## Missing Verification

- Run `aiflow verify` or explain why verification was not run.

## Suggested Checks

- Check behavior changes against affected modules.
- Check tests for changed production code.
- Check project-specific risk paths before release.
"""
    path, status_text = write_text_safely(output_path, report, force=True)
    payload = {
        "ok": True,
        "generated_at": now_stamp(),
        "changed_files": changed_files,
        "high_risk_signals": risks,
        "findings": [],
        "blocking": False,
    }
    write_json(output_dir / "review.json", payload)
    return {"path": str(path), "status_text": status_text, **payload}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

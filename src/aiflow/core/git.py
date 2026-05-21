from __future__ import annotations

import subprocess
from pathlib import Path


def git_available(root: Path) -> bool:
    return run_git(root, ["rev-parse", "--is-inside-work-tree"]).returncode == 0


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)


def git_lines(root: Path, args: list[str]) -> list[str]:
    result = run_git(root, args)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]

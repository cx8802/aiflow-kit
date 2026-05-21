from __future__ import annotations

import subprocess
from pathlib import Path


IGNORED_DIRS = {
    ".git",
    ".cache",
    ".tools",
    ".venv",
    "node_modules",
    "dist",
    "build",
    ".next",
    "__pycache__",
}


def project_root(start: Path | None = None) -> Path:
    cwd = (start or Path.cwd()).resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=True,
        )
        return Path(result.stdout.strip()).resolve()
    except Exception:
        return cwd


def aiflow_dir(root: Path) -> Path:
    return root / ".aiflow"


def ensure_aiflow_dir(root: Path) -> Path:
    path = aiflow_dir(root)
    path.mkdir(parents=True, exist_ok=True)
    return path

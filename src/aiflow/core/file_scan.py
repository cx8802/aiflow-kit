from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
import os

from .paths import IGNORED_DIRS


def list_project_files(root: Path, *, limit: int = 200, exclude: list[str] | None = None) -> tuple[list[str], str]:
    excluded = sorted(set(IGNORED_DIRS).union(exclude or []))
    if shutil.which("rg"):
        env = os.environ.copy()
        env["RG_COLOR"] = "never"
        command = ["rg", "--files", "--hidden", "--glob", "!.git/**"]
        for item in excluded:
            normalized = item.strip().replace("\\", "/").rstrip("/")
            if normalized and normalized != ".git":
                command.extend(["--glob", f"!{normalized}/**"])
        result = subprocess.run(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if result.returncode in (0, 1):
            files = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
            return files[:limit], "ripgrep"
    return list_project_files_python(root, limit=limit, exclude=excluded), "python"


def list_project_files_python(root: Path, *, limit: int, exclude: list[str]) -> list[str]:
    files: list[str] = []
    excluded = {item.strip().replace("\\", "/").rstrip("/") for item in exclude}
    for path in root.rglob("*"):
        if len(files) >= limit:
            break
        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts):
            continue
        if path.is_file():
            files.append(relative.as_posix())
    return files

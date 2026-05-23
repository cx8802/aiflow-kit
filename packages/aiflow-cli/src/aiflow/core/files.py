from __future__ import annotations

import filecmp
import shutil
from pathlib import Path


def write_text_safely(path: Path, content: str, *, force: bool = False) -> tuple[Path, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        if path.read_text(encoding="utf-8") == content:
            return path, "unchanged"
        new_path = path.with_name(path.name + ".new")
        new_path.write_text(content, encoding="utf-8", newline="\n")
        return new_path, "created-new"
    path.write_text(content, encoding="utf-8", newline="\n")
    return path, "written"


def copy_tree_safely(src: Path, dst: Path, *, force: bool = False) -> str:
    if dst.exists():
        if force:
            shutil.rmtree(dst)
        elif dirs_equal(src, dst):
            return "unchanged"
        else:
            return "conflict"
    shutil.copytree(src, dst)
    return "written"


def dirs_equal(left: Path, right: Path) -> bool:
    cmp = filecmp.dircmp(left, right)
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(dirs_equal(left / sub, right / sub) for sub in cmp.common_dirs)

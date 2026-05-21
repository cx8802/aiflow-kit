from __future__ import annotations

import json
import os
import shutil
from argparse import Namespace
from pathlib import Path

from ..core.config import load_config
from ..core.environment import render_runtime_text
from ..core.files import copy_tree_safely
from ..core.paths import ensure_aiflow_dir, project_root
from ..core.resources import skills_root


PLUGIN_NAME = "aiflow-kit"


def run_install_skills(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    config = load_config(root)

    targets = expand_targets(args.target)
    reports: list[str] = []
    has_conflict = False
    for target in targets:
        if target in {"codex-user", "claude-user"}:
            if not args.confirm_global:
                print("Refusing user-level install without --confirm-global.")
                return 2
            if not config.get("skills", {}).get("allow_global_install", False) and not args.allow_global:
                print("Refusing user-level install because allow_global_install=false in .aiflow/config.toml.")
                print("For bundled generic aiflow skills, rerun with --confirm-global --allow-global.")
                return 2
        target_reports = install_target(root, target, args.output, force=args.force)
        has_conflict = has_conflict or any(": conflict " in line or "use --force" in line for line in target_reports)
        reports.extend(target_reports)

    print("Skill install report:")
    for line in reports:
        print(f"- {line}")
    return 1 if has_conflict else 0


def expand_targets(target: str) -> list[str]:
    if target == "all":
        return ["codex-repo", "claude-plugin", "codex-plugin"]
    return [target]


def install_target(root: Path, target: str, output: Path | None, *, force: bool) -> list[str]:
    if target == "codex-repo":
        return copy_skills_to(root / ".agents" / "skills", force=force, label="project codex skills")
    if target == "codex-user":
        home = Path(os.path.expanduser("~"))
        return copy_skills_to(home / ".agents" / "skills", force=force, label="user codex skills")
    if target == "claude-user":
        home = Path(os.path.expanduser("~"))
        return copy_skills_to(home / ".claude" / "skills", force=force, label="user claude skills")
    if target == "claude-plugin":
        out = output or (root / ".aiflow" / "dist" / "claude")
        return create_plugin(out, ".claude-plugin", claude_manifest(), force=force, label="claude plugin")
    if target == "codex-plugin":
        out = output or (root / ".aiflow" / "dist" / "codex")
        return create_plugin(out, ".codex-plugin", codex_manifest(), force=force, label="codex plugin")
    raise ValueError(f"Unknown target: {target}")


def copy_skills_to(dst_root: Path, *, force: bool, label: str) -> list[str]:
    reports: list[str] = []
    src_root = Path(str(skills_root()))
    root = project_root()
    dst_root.mkdir(parents=True, exist_ok=True)
    for skill in sorted(src_root.iterdir(), key=lambda p: p.name):
        if not skill.is_dir():
            continue
        status = copy_skill_tree_safely(skill, dst_root / skill.name, root=root, force=force)
        reports.append(f"{label}: {status} {dst_root / skill.name}")
        if status == "conflict":
            reports.append(f"{label}: use --force to overwrite {dst_root / skill.name}")
    return reports


def copy_skill_tree_safely(src: Path, dst: Path, *, root: Path, force: bool = False) -> str:
    if not has_runtime_placeholders(src):
        return copy_tree_safely(src, dst, force=force)
    if dst.exists():
        if force:
            shutil.rmtree(dst)
        elif rendered_dirs_equal(src, dst, root):
            return "unchanged"
        else:
            return "conflict"
    copy_tree_rendered(src, dst, root)
    return "written"


def has_runtime_placeholders(src: Path) -> bool:
    for file in src.rglob("*"):
        if file.is_file() and file.suffix.lower() in {".md", ".json", ".toml"}:
            if "{{ AIFLOW_" in file.read_text(encoding="utf-8"):
                return True
    return False


def rendered_dirs_equal(src: Path, dst: Path, root: Path) -> bool:
    src_files = sorted(path.relative_to(src) for path in src.rglob("*") if path.is_file())
    dst_files = sorted(path.relative_to(dst) for path in dst.rglob("*") if path.is_file()) if dst.exists() else []
    if src_files != dst_files:
        return False
    for rel in src_files:
        src_file = src / rel
        dst_file = dst / rel
        if src_file.suffix.lower() in {".md", ".json", ".toml"}:
            expected = render_runtime_text(src_file.read_text(encoding="utf-8"), root)
            if not dst_file.exists() or dst_file.read_text(encoding="utf-8") != expected:
                return False
        elif not dst_file.exists() or src_file.read_bytes() != dst_file.read_bytes():
            return False
    return True


def copy_tree_rendered(src: Path, dst: Path, root: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if item.suffix.lower() in {".md", ".json", ".toml"}:
            target.write_text(render_runtime_text(item.read_text(encoding="utf-8"), root), encoding="utf-8", newline="\n")
        else:
            shutil.copy2(item, target)


def create_plugin(out: Path, manifest_dir_name: str, manifest: dict, *, force: bool, label: str) -> list[str]:
    reports = copy_skills_to(out / "skills", force=force, label=f"{label} skills")
    manifest_dir = out / manifest_dir_name
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "plugin.json"
    if manifest_path.exists() and not force:
        existing = manifest_path.read_text(encoding="utf-8")
        desired = json.dumps(manifest, indent=2) + "\n"
        if existing == desired:
            reports.append(f"{label}: unchanged {manifest_path}")
        else:
            reports.append(f"{label}: conflict {manifest_path}")
            reports.append(f"{label}: use --force to overwrite {manifest_path}")
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        reports.append(f"{label}: written {manifest_path}")
    return reports


def claude_manifest() -> dict:
    return {
        "name": PLUGIN_NAME,
        "description": "AI coding workflow skills for analysis, planning, implementation, verification, review, and release.",
        "version": "0.1.0",
        "author": {"name": PLUGIN_NAME},
    }


def codex_manifest() -> dict:
    return {
        "name": PLUGIN_NAME,
        "version": "0.1.0",
        "description": "Reusable AI coding workflow skills.",
        "skills": "./skills/",
    }

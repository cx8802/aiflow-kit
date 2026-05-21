from __future__ import annotations

import json
from pathlib import Path

from .config import load_config
from .file_scan import list_project_files
from .markdown import bullet, now_stamp
from .paths import IGNORED_DIRS


TECH_MARKERS = {
    "Python": ["pyproject.toml", "requirements.txt", "setup.py"],
    "Node": ["package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json"],
    "Go": ["go.mod"],
    "Java/Maven": ["pom.xml"],
    "Java/Gradle": ["build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"],
    "Rust": ["Cargo.toml"],
}


def detect_tech(root: Path) -> list[str]:
    found: list[str] = []
    for tech, markers in TECH_MARKERS.items():
        if any((root / marker).exists() for marker in markers):
            found.append(tech)
    return found


def top_level_dirs(root: Path) -> list[str]:
    dirs = []
    for item in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if item.is_dir() and item.name not in IGNORED_DIRS:
            dirs.append(item.name + "/")
    return dirs


def important_files(root: Path) -> list[str]:
    names = [
        "README.md",
        "pyproject.toml",
        "package.json",
        "go.mod",
        "pom.xml",
        "AGENTS.md",
        "CLAUDE.md",
        ".aiflow/config.toml",
    ]
    return [name for name in names if (root / name).exists()]


def suggested_commands(root: Path, config: dict) -> list[str]:
    configured = []
    for name, command in config.get("commands", {}).items():
        if command:
            configured.append(f"{name}: `{command}`")
    if configured:
        return configured

    suggestions: list[str] = []
    package_json = root / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})
            for key in ["lint", "typecheck", "test", "build", "dev"]:
                if key in scripts:
                    suggestions.append(f"{key}: `npm.cmd run {key}`")
        except Exception:
            pass
    if (root / "pyproject.toml").exists():
        suggestions.append("python: `python -m pytest` if pytest is configured")
    if (root / "go.mod").exists():
        suggestions.append("go test: `go test ./...`")
    if (root / "pom.xml").exists():
        suggestions.append("maven test: `mvn test`")
    return suggestions


def build_context_report(root: Path) -> str:
    config = load_config(root)
    files, scan_method = list_project_files(root, limit=80, exclude=config.get("context", {}).get("exclude", []))
    return f"""# Project Context

## Generated At

{now_stamp()}

## Project

- Name: {config.get("project", {}).get("name", root.name)}
- Root: `{root}`

## Tech Stack

{bullet(detect_tech(root))}
## Important Directories

{bullet(top_level_dirs(root))}
## Important Files

{bullet(important_files(root))}
## File Scan

- Method: {scan_method}
- Limit: 80 files

{bullet([f"`{path}`" for path in files])}
## Commands

{bullet(suggested_commands(root, config))}
## Risk Areas

{bullet(config.get("review", {}).get("high_risk_paths", []))}
## Notes for AI Agents

- Read `AGENTS.md` and `CLAUDE.md` when present.
- Keep project-specific commands and generated context inside this repository.
- Do not write user-global configuration unless explicitly requested.
"""

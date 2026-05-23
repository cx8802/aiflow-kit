from __future__ import annotations

import os
from pathlib import Path

from .config import load_config
from .markdown import bullet, now_stamp
from .project_scan import build_context_report


SECRET_HINTS = (
    "password",
    "passwd",
    "pwd=",
    "token",
    "secret",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "密码",
    "口令",
    "密钥",
)


COMPACT_SOURCES = (
    ".aiflow/context.md",
    ".aiflow/memory.md",
    ".aiflow/plan.md",
    ".aiflow/verify.md",
    ".aiflow/review.md",
    ".aiflow/agents/status.md",
)


def project_memory_path(root: Path) -> Path:
    config = load_config(root)
    configured = config.get("memory", {}).get("project_file", ".aiflow/memory.md")
    return root / configured


def compact_context_path(root: Path) -> Path:
    config = load_config(root)
    configured = config.get("memory", {}).get("compact_file", ".aiflow/context.compact.md")
    return root / configured


def global_memory_path() -> Path:
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    return home / ".aiflow" / "memory.md"


def memory_path(root: Path, *, global_scope: bool = False) -> Path:
    return global_memory_path() if global_scope else project_memory_path(root)


def has_secret_hint(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in SECRET_HINTS)


def add_memory_entry(root: Path, text: str, *, global_scope: bool = False, tags: list[str] | None = None) -> Path:
    path = memory_path(root, global_scope=global_scope)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        scope = "Global" if global_scope else "Project"
        path.write_text(f"# {scope} Memory\n\n## Entries\n\n", encoding="utf-8", newline="\n")

    clean_text = " ".join(text.split())
    tag_text = ""
    if tags:
        tag_text = " " + " ".join(f"#{tag.strip()}" for tag in tags if tag.strip())
    entry = f"- {now_stamp()} {clean_text}{tag_text}\n"
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(entry)
    return path


def list_memory_entries(root: Path, *, global_scope: bool = False, limit: int = 50) -> list[str]:
    path = memory_path(root, global_scope=global_scope)
    if not path.exists():
        return []
    entries = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip().startswith("- ")]
    return entries[-limit:]


def search_memory_entries(root: Path, query: str, *, global_scope: bool = False, limit: int = 50) -> list[str]:
    lowered = query.lower()
    matches = [entry for entry in list_memory_entries(root, global_scope=global_scope, limit=1000) if lowered in entry.lower()]
    return matches[-limit:]


def write_compact_context(root: Path, *, output: Path | None = None, refresh_context: bool = False) -> Path:
    aiflow_dir = root / ".aiflow"
    aiflow_dir.mkdir(parents=True, exist_ok=True)
    context_file = aiflow_dir / "context.md"
    if refresh_context or not context_file.exists():
        context_file.write_text(build_context_report(root), encoding="utf-8", newline="\n")

    target = output or compact_context_path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_compact_context(root), encoding="utf-8", newline="\n")
    return target


def build_compact_context(root: Path) -> str:
    config = load_config(root)
    try:
        max_entries = int(config.get("memory", {}).get("max_compact_entries", 30))
    except (TypeError, ValueError):
        max_entries = 30
    max_entries = max(max_entries, 1)
    context = read_project_file(root, ".aiflow/context.md")
    memory = list_memory_entries(root, limit=max_entries)
    global_memory = list_memory_entries(root, global_scope=True, limit=min(max_entries, 20))

    sections = [
        "# Compact Context",
        "",
        "## Generated At",
        "",
        now_stamp(),
        "",
        "## Scope",
        "",
        f"- Project root: `{root}`",
        "- Prefer this file for fast orientation, then open full source files only when needed.",
        "- Do not store secrets in memory or compact context.",
        "",
        "## Sources",
        "",
        bullet([source for source in COMPACT_SOURCES if (root / source).exists()]),
        "## Project",
        "",
        compact_context_sections(
            context,
            [
                "Project",
                "Tech Stack",
                "Important Directories",
                "Important Files",
                "Commands",
                "Risk Areas",
            ],
            max_lines_per_section=20,
        ),
        "## Project Memory",
        "",
        format_entry_lines(memory),
        "## Global Memory",
        "",
        format_entry_lines(global_memory),
        "## Current Plan",
        "",
        compact_markdown(read_project_file(root, ".aiflow/plan.md"), max_lines=50),
        "## Verification",
        "",
        compact_markdown(read_project_file(root, ".aiflow/verify.md"), max_lines=40),
        "## Review",
        "",
        compact_markdown(read_project_file(root, ".aiflow/review.md"), max_lines=30),
        "## Agent Status",
        "",
        compact_markdown(read_project_file(root, ".aiflow/agents/status.md"), max_lines=40),
        "## Operating Rules",
        "",
        "- Read `AGENTS.md` and `CLAUDE.md` when present.",
        "- Keep project-specific facts inside this repository.",
        "- Use explicit global memory only for reusable user preferences.",
        "- Use `.aiflow/*.local.toml` for secrets, not memory files.",
        "",
    ]
    return "\n".join(sections)


def read_project_file(root: Path, relative: str) -> str:
    path = root / relative
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def compact_context_sections(text: str, names: list[str], *, max_lines_per_section: int) -> str:
    if not text:
        return "- None\n"
    parts: list[str] = []
    for name in names:
        section = extract_h2_section(text, name)
        if not section:
            continue
        parts.append(f"### {name}")
        parts.append("")
        parts.append(limit_markdown_lines(section, max_lines_per_section))
    return "\n".join(parts).strip() + "\n" if parts else "- None\n"


def extract_h2_section(text: str, name: str) -> str:
    lines = text.splitlines()
    capture = False
    captured: list[str] = []
    heading = f"## {name}"
    for line in lines:
        if line.strip() == heading:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            captured.append(line)
    return "\n".join(captured).strip()


def compact_markdown(text: str, *, max_lines: int) -> str:
    if not text.strip():
        return "- None\n"
    return limit_markdown_lines(text, max_lines)


def format_entry_lines(entries: list[str]) -> str:
    if not entries:
        return "- None\n"
    return "\n".join(entries).strip() + "\n"


def limit_markdown_lines(text: str, max_lines: int) -> str:
    kept: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        kept.append(line)
        if len(kept) >= max_lines:
            kept.append("- ... truncated")
            break
    return "\n".join(kept).strip() + "\n"

from __future__ import annotations

from importlib import resources

from .environment import aiflow_kit_root


def read_template(name: str) -> str:
    return (resources.files("aiflow") / "assets" / "templates" / name).read_text(encoding="utf-8")


def skills_root():
    return resources.files("aiflow") / "assets" / "skills"


def browser_extension_root():
    source_root = aiflow_kit_root() / "extensions" / "browser"
    if source_root.exists():
        return source_root
    return resources.files("aiflow") / "assets" / "browser_extension"

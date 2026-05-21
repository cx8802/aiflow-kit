from __future__ import annotations

from importlib import resources


def read_template(name: str) -> str:
    return (resources.files("aiflow") / "assets" / "templates" / name).read_text(encoding="utf-8")


def skills_root():
    return resources.files("aiflow") / "assets" / "skills"

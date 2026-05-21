from __future__ import annotations

from datetime import datetime


def now_stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def bullet(items: list[str]) -> str:
    if not items:
        return "- None\n"
    return "".join(f"- {item}\n" for item in items)

from __future__ import annotations

import sqlite3
import tomllib
from pathlib import Path
from typing import Any


DATABASE_TYPES = ["sqlite", "mysql", "postgres", "sqlserver", "oracle", "mongodb"]


def database_config_path(root: Path) -> Path:
    return root / ".aiflow" / "databases.toml"


def database_local_path(root: Path) -> Path:
    return root / ".aiflow" / "databases.local.toml"


def load_database_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"databases": {}}
    with path.open("rb") as f:
        data = tomllib.load(f)
    data.setdefault("databases", {})
    return data


def load_databases(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return load_database_file(database_config_path(root)), load_database_file(database_local_path(root))


def save_database_file(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_toml(data), encoding="utf-8", newline="\n")


def dumps_toml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    databases = data.get("databases", {})
    for name in sorted(databases):
        lines.append(f"[databases.{name}]")
        for key, value in databases[name].items():
            if value is None or value == "":
                continue
            lines.append(f"{key} = {format_toml_value(value)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def redact_profile(name: str, config_profile: dict[str, Any], local_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    local_profile = local_profile or {}
    result = {"name": name, **config_profile}
    for key in ["dsn", "user", "password"]:
        if key in local_profile:
            result[f"{key}_local"] = "***"
    return result


def sqlite_test(path: Path) -> tuple[bool, str]:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.execute("select 1")
        conn.close()
        return True, f"sqlite ok: {path}"
    except Exception as exc:
        return False, f"sqlite failed: {exc}"

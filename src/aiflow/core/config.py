from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "project": {"name": "", "type": "auto"},
    "commands": {"install": "", "lint": "", "typecheck": "", "test": "", "build": "", "dev": ""},
    "context": {
        "include": ["README.md", "package.json", "pyproject.toml", "go.mod", "pom.xml", "src", "docs", "tests"],
        "exclude": [".git", ".cache", ".tools", ".venv", "node_modules", "dist", "build", ".next"],
    },
    "frontend": {
        "enabled": False,
        "dev_url": "http://localhost:3000",
        "desktop_viewport": "1440x900",
        "mobile_viewport": "390x844",
    },
    "review": {
        "require_tests": True,
        "require_verification_summary": True,
        "high_risk_paths": ["auth/", "security/", "payment/", "database/", "migrations/"],
    },
    "skills": {
        "install_to_codex_repo": True,
        "install_to_codex_user": False,
        "install_to_claude_user": False,
        "install_to_claude_plugin": True,
        "allow_global_install": False,
    },
}


def config_path(root: Path) -> Path:
    return root / ".aiflow" / "config.toml"


def load_config(root: Path) -> dict[str, Any]:
    path = config_path(root)
    config = deep_copy(DEFAULT_CONFIG)
    if path.exists():
        with path.open("rb") as f:
            user_config = tomllib.load(f)
        deep_merge(config, user_config)
    if not config["project"].get("name"):
        config["project"]["name"] = root.name
    return config


def deep_copy(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: deep_copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return list(value)
    return value


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = value

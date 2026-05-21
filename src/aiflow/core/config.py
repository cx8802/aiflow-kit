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
    "memory": {
        "enabled": True,
        "project_file": ".aiflow/memory.md",
        "compact_file": ".aiflow/context.compact.md",
        "max_compact_entries": 30,
    },
    "claude_agent": {
        "enabled": False,
        "runtime": "node",
        "package_dir": ".tools/claude-agent",
        "runner": "node/claude-agent-runner/runner.mjs",
        "default_model": "small",
        "small_model": "",
        "standard_model": "",
        "strong_model": "",
        "api_key_env": "ANTHROPIC_API_KEY",
        "base_url_env": "ANTHROPIC_BASE_URL",
        "auth_token_env": "",
        "proxy_mode": "auto",
        "overseas_proxy": "http://127.0.0.1:10808",
        "china_direct": True,
        "permission_mode": "dontAsk",
        "allowed_tools": ["Read", "Glob", "Grep"],
        "disallowed_tools": ["Bash", "Edit", "Write"],
        "max_turns": 8,
        "max_budget_usd": 0.20,
        "timeout_seconds": 300,
        "runs_dir": ".aiflow/claude-agent/runs",
        "sessions_dir": ".aiflow/claude-agent/sessions",
        "usage_file": ".aiflow/claude-agent/usage.jsonl",
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


def load_config_file(root: Path) -> dict[str, Any]:
    path = config_path(root)
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def save_config(root: Path, config: dict[str, Any]) -> Path:
    path = config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_toml(config), encoding="utf-8", newline="\n")
    return path


def get_config_value(config: dict[str, Any], dotted_key: str) -> Any:
    current: Any = config
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_key)
        current = current[part]
    return current


def set_config_value(config: dict[str, Any], dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    if not parts or any(not part for part in parts):
        raise KeyError(dotted_key)
    current: dict[str, Any] = config
    for part in parts[:-1]:
        next_value = current.setdefault(part, {})
        if not isinstance(next_value, dict):
            raise TypeError(f"Cannot set nested key under non-table value: {part}")
        current = next_value
    current[parts[-1]] = value


def parse_config_value(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)
    try:
        if "." in value:
            return float(value)
    except ValueError:
        pass
    if value.startswith("[") and value.endswith("]"):
        parsed = tomllib.loads(f"value = {value}\n")
        return parsed["value"]
    return value


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    allowed_sections = set(DEFAULT_CONFIG)
    for section in config:
        if section not in allowed_sections:
            errors.append(f"Unknown section: {section}")

    project = config.get("project", {})
    if not isinstance(project, dict):
        errors.append("project must be a table")
    else:
        require_str(project, "name", "project.name", errors, allow_empty=True)
        require_str(project, "type", "project.type", errors)

    commands = config.get("commands", {})
    if not isinstance(commands, dict):
        errors.append("commands must be a table")
    else:
        for key in DEFAULT_CONFIG["commands"]:
            require_str(commands, key, f"commands.{key}", errors, allow_empty=True)

    context = config.get("context", {})
    if not isinstance(context, dict):
        errors.append("context must be a table")
    else:
        require_str_list(context, "include", "context.include", errors)
        require_str_list(context, "exclude", "context.exclude", errors)

    memory = config.get("memory", {})
    if not isinstance(memory, dict):
        errors.append("memory must be a table")
    else:
        require_bool(memory, "enabled", "memory.enabled", errors)
        require_str(memory, "project_file", "memory.project_file", errors)
        require_str(memory, "compact_file", "memory.compact_file", errors)
        require_int(memory, "max_compact_entries", "memory.max_compact_entries", errors)

    claude_agent = config.get("claude_agent", {})
    if not isinstance(claude_agent, dict):
        errors.append("claude_agent must be a table")
    else:
        require_bool(claude_agent, "enabled", "claude_agent.enabled", errors)
        for key in [
            "runtime",
            "package_dir",
            "runner",
            "default_model",
            "small_model",
            "standard_model",
            "strong_model",
            "api_key_env",
            "base_url_env",
            "auth_token_env",
            "proxy_mode",
            "overseas_proxy",
            "permission_mode",
            "runs_dir",
            "sessions_dir",
            "usage_file",
        ]:
            allow_empty = key in {"small_model", "standard_model", "strong_model", "auth_token_env"}
            require_str(claude_agent, key, f"claude_agent.{key}", errors, allow_empty=allow_empty)
        require_bool(claude_agent, "china_direct", "claude_agent.china_direct", errors)
        require_str_list(claude_agent, "allowed_tools", "claude_agent.allowed_tools", errors)
        require_str_list(claude_agent, "disallowed_tools", "claude_agent.disallowed_tools", errors)
        require_int(claude_agent, "max_turns", "claude_agent.max_turns", errors)
        require_number(claude_agent, "max_budget_usd", "claude_agent.max_budget_usd", errors)
        require_int(claude_agent, "timeout_seconds", "claude_agent.timeout_seconds", errors)

    frontend = config.get("frontend", {})
    if not isinstance(frontend, dict):
        errors.append("frontend must be a table")
    else:
        require_bool(frontend, "enabled", "frontend.enabled", errors)
        require_str(frontend, "dev_url", "frontend.dev_url", errors)
        require_str(frontend, "desktop_viewport", "frontend.desktop_viewport", errors)
        require_str(frontend, "mobile_viewport", "frontend.mobile_viewport", errors)

    review = config.get("review", {})
    if not isinstance(review, dict):
        errors.append("review must be a table")
    else:
        require_bool(review, "require_tests", "review.require_tests", errors)
        require_bool(review, "require_verification_summary", "review.require_verification_summary", errors)
        require_str_list(review, "high_risk_paths", "review.high_risk_paths", errors)

    skills = config.get("skills", {})
    if not isinstance(skills, dict):
        errors.append("skills must be a table")
    else:
        for key in DEFAULT_CONFIG["skills"]:
            require_bool(skills, key, f"skills.{key}", errors)

    return errors


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


def dumps_toml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for section, values in data.items():
        if isinstance(values, dict):
            lines.append(f"[{section}]")
            for key, value in values.items():
                if isinstance(value, dict):
                    continue
                lines.append(f"{key} = {format_toml_value(value)}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(format_toml_value(item) for item in value) + "]"
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def require_str(table: dict[str, Any], key: str, label: str, errors: list[str], *, allow_empty: bool = False) -> None:
    value = table.get(key)
    if not isinstance(value, str):
        errors.append(f"{label} must be a string")
    elif not allow_empty and not value:
        errors.append(f"{label} must not be empty")


def require_bool(table: dict[str, Any], key: str, label: str, errors: list[str]) -> None:
    if not isinstance(table.get(key), bool):
        errors.append(f"{label} must be a boolean")


def require_int(table: dict[str, Any], key: str, label: str, errors: list[str]) -> None:
    if not isinstance(table.get(key), int):
        errors.append(f"{label} must be an integer")


def require_number(table: dict[str, Any], key: str, label: str, errors: list[str]) -> None:
    value = table.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{label} must be a number")


def require_str_list(table: dict[str, Any], key: str, label: str, errors: list[str]) -> None:
    value = table.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{label} must be a string list")

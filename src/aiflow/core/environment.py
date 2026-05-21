from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from .markdown import now_stamp


TOOLS = {
    "git": ["git", "--version"],
    "ripgrep": ["rg", "--version"],
    "python": [sys.executable, "--version"],
    "go": ["go", "version"],
    "node": ["node", "--version"],
    "npm": ["npm.cmd" if os.name == "nt" else "npm", "--version"],
    "java": ["java", "-version"],
    "maven": ["mvn", "--version"],
}


def env_local_path(root: Path) -> Path:
    return root / ".aiflow" / "env.local.toml"


def aiflow_kit_root() -> Path:
    env_root = os.environ.get("AIFLOW_KIT_ROOT")
    if env_root:
        return Path(env_root).resolve()

    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "scripts" / "aiflow-dev.bat").exists() and (parent / "src" / "aiflow").exists():
            return parent
    return current.parents[3]


def detect_environment(project_root: Path) -> dict[str, Any]:
    kit_root = aiflow_kit_root()
    data: dict[str, Any] = {
        "generated_at": now_stamp(),
        "paths": {
            "project_root": str(project_root),
            "aiflow_kit_root": str(kit_root),
            "scripts_dir": str(kit_root / "scripts"),
            "aiflow_dev_bat": str(kit_root / "scripts" / "aiflow-dev.bat"),
            "aiflow_update_bat": str(kit_root / "scripts" / "aiflow-update.bat"),
            "use_project_env_bat": str(kit_root / "scripts" / "use-project-env.bat"),
            "cache_root": str(project_root / ".cache"),
            "tools_root": str(project_root / ".tools"),
            "python_venv": str(project_root / ".venv"),
            "claude_plugin_dir": str(kit_root / ".aiflow" / "dist" / "claude"),
            "codex_plugin_dir": str(kit_root / ".aiflow" / "dist" / "codex"),
        },
        "proxy": {
            "overseas_url": os.environ.get("AIFLOW_PROXY_URL", "http://127.0.0.1:10808"),
            "china_direct": True,
            "scope": "current cmd session only",
        },
        "tools": {},
    }
    tools = data["tools"]
    for name, command in TOOLS.items():
        executable = command[0]
        path = sys.executable if name == "python" else shutil.which(executable)
        version_command = [str(path), *command[1:]] if path else command
        version = command_version(version_command) if path else ""
        tools[name] = {
            "command": executable,
            "path": str(path or ""),
            "status": "ok" if path else "missing",
            "version": version,
        }
    return data


def command_version(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=10,
        )
    except Exception as exc:
        return f"error: {exc}"
    output = "\n".join(part for part in [result.stdout, result.stderr] if part).strip()
    return output.splitlines()[0].strip() if output else ""


def write_env_config(root: Path, data: dict[str, Any]) -> Path:
    path = env_local_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_env_toml(data), encoding="utf-8", newline="\n")
    return path


def load_env_config(root: Path) -> dict[str, Any]:
    path = env_local_path(root)
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def runtime_values(project_root: Path) -> dict[str, str]:
    data = load_env_config(project_root)
    paths = data.get("paths", {}) if isinstance(data, dict) else {}
    kit_root = Path(paths.get("aiflow_kit_root") or aiflow_kit_root()).resolve()
    return {
        "AIFLOW_KIT_ROOT": str(kit_root),
        "AIFLOW_SCRIPTS_DIR": str(kit_root / "scripts"),
        "AIFLOW_DEV_BAT": str(kit_root / "scripts" / "aiflow-dev.bat"),
        "AIFLOW_UPDATE_BAT": str(kit_root / "scripts" / "aiflow-update.bat"),
        "AIFLOW_USE_PROJECT_ENV_BAT": str(kit_root / "scripts" / "use-project-env.bat"),
        "AIFLOW_CLAUDE_PLUGIN_DIR": str(kit_root / ".aiflow" / "dist" / "claude"),
        "AIFLOW_CODEX_PLUGIN_DIR": str(kit_root / ".aiflow" / "dist" / "codex"),
    }


def render_runtime_text(text: str, project_root: Path) -> str:
    rendered = text
    for key, value in runtime_values(project_root).items():
        rendered = rendered.replace("{{ " + key + " }}", value)
    return rendered


def env_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# Environment",
        "",
        f"Generated at: {data.get('generated_at', '')}",
        "",
        "## Paths",
        "",
    ]
    paths = data.get("paths", {})
    for key in sorted(paths):
        lines.append(f"- `{key}`: `{paths[key]}`")
    lines.extend(["", "## Tools", "", "| Tool | Status | Path | Version |", "| --- | --- | --- | --- |"])
    for name, info in data.get("tools", {}).items():
        lines.append(f"| `{name}` | {info.get('status', '')} | `{info.get('path', '')}` | `{info.get('version', '')}` |")
    proxy = data.get("proxy", {})
    lines.extend(
        [
            "",
            "## Proxy",
            "",
            f"- overseas_url: `{proxy.get('overseas_url', '')}`",
            f"- china_direct: `{proxy.get('china_direct', '')}`",
            f"- scope: `{proxy.get('scope', '')}`",
            "",
        ]
    )
    return "\n".join(lines)


def dumps_env_toml(data: dict[str, Any]) -> str:
    lines = [f"generated_at = {toml_string(str(data.get('generated_at', '')))}", ""]
    lines.append("[paths]")
    for key, value in data.get("paths", {}).items():
        lines.append(f"{key} = {toml_string(str(value))}")
    lines.extend(["", "[proxy]"])
    for key, value in data.get("proxy", {}).items():
        lines.append(f"{key} = {toml_value(value)}")
    for name, info in data.get("tools", {}).items():
        lines.extend(["", f"[tools.{name}]"])
        for key, value in info.items():
            lines.append(f"{key} = {toml_string(str(value))}")
    return "\n".join(lines).rstrip() + "\n"


def toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return toml_string(str(value))


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

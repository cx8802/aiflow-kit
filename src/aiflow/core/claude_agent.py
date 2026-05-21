from __future__ import annotations

import json
import os
import shutil
import subprocess
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import load_config
from .environment import aiflow_kit_root


SDK_PACKAGE = "@anthropic-ai/claude-agent-sdk"
MODEL_ALIASES = {
    "small": "small_model",
    "standard": "standard_model",
    "strong": "strong_model",
}


def claude_agent_config(root: Path) -> dict[str, Any]:
    return load_config(root).get("claude_agent", {})


def package_dir(root: Path, config: dict[str, Any]) -> Path:
    configured = Path(str(config.get("package_dir", ".tools/claude-agent")))
    return configured if configured.is_absolute() else aiflow_kit_root() / configured


def runs_dir(root: Path, config: dict[str, Any]) -> Path:
    return resolve_project_path(root, str(config.get("runs_dir", ".aiflow/claude-agent/runs")))


def sessions_dir(root: Path, config: dict[str, Any]) -> Path:
    return resolve_project_path(root, str(config.get("sessions_dir", ".aiflow/claude-agent/sessions")))


def usage_file(root: Path, config: dict[str, Any]) -> Path:
    return resolve_project_path(root, str(config.get("usage_file", ".aiflow/claude-agent/usage.jsonl")))


def local_env_path(root: Path) -> Path:
    return root / ".aiflow" / "claude-agent.local.toml"


def runner_path(root: Path, config: dict[str, Any]) -> Path:
    configured = Path(str(config.get("runner", "node/claude-agent-runner/runner.mjs")))
    if configured.is_absolute():
        return configured
    project_runner = root / configured
    if project_runner.exists():
        return project_runner
    return aiflow_kit_root() / configured


def resolve_project_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def resolve_model(config: dict[str, Any], requested: str | None) -> tuple[str, str | None]:
    name = requested or str(config.get("default_model", "small"))
    key = MODEL_ALIASES.get(name)
    if key:
        value = str(config.get(key, "")).strip()
        if not value:
            return "", f"claude_agent.{key} is empty. Configure it with: aiflow config set claude_agent.{key} \"<model-name>\""
        return value, None
    return name, None


def node_command() -> str | None:
    return shutil.which("node.exe" if os.name == "nt" else "node") or shutil.which("node")


def npm_command() -> str | None:
    return shutil.which("npm.cmd" if os.name == "nt" else "npm") or shutil.which("npm")


def claude_code_command() -> str | None:
    return shutil.which("claude.exe" if os.name == "nt" else "claude") or shutil.which("claude")


def sdk_installed(root: Path, config: dict[str, Any]) -> bool:
    return (package_dir(root, config) / "node_modules" / "@anthropic-ai" / "claude-agent-sdk").exists()


def ensure_package_json(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    package_json = path / "package.json"
    if not package_json.exists():
        package_json.write_text(
            json.dumps({"private": True, "type": "module", "dependencies": {}}, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return package_json


def load_local_env(root: Path) -> dict[str, str]:
    path = local_env_path(root)
    if not path.exists():
        return {}
    with path.open("rb") as file:
        data = tomllib.load(file)
    env = data.get("env", {})
    if not isinstance(env, dict):
        return {}
    return {str(key): str(value) for key, value in env.items() if isinstance(value, (str, int, float, bool))}


def make_run_id(task: str) -> str:
    safe_task = "".join(ch if ch.isalnum() else "-" for ch in task.lower()).strip("-") or "run"
    safe_task = "-".join(part for part in safe_task.split("-") if part)[:40]
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{safe_task}"


def default_context_files(root: Path) -> list[str]:
    candidates = [
        ".aiflow/context.compact.md",
        ".aiflow/context.md",
        ".aiflow/memory.md",
        "AGENTS.md",
        "CLAUDE.md",
    ]
    return [relative for relative in candidates if (root / relative).exists()]


def command_env(root: Path, config: dict[str, Any], *, use_proxy: bool) -> dict[str, str]:
    env = os.environ.copy()
    env.update(load_local_env(root))
    api_key_env = str(config.get("api_key_env", "ANTHROPIC_API_KEY"))
    base_url_env = str(config.get("base_url_env", "ANTHROPIC_BASE_URL"))
    auth_token_env = str(config.get("auth_token_env", ""))

    if api_key_env and api_key_env != "ANTHROPIC_API_KEY" and env.get(api_key_env):
        env["ANTHROPIC_API_KEY"] = env[api_key_env]
    if base_url_env and base_url_env != "ANTHROPIC_BASE_URL" and env.get(base_url_env):
        env["ANTHROPIC_BASE_URL"] = env[base_url_env]
    if auth_token_env and env.get(auth_token_env):
        env["ANTHROPIC_AUTH_TOKEN"] = env[auth_token_env]

    if use_proxy:
        proxy = str(config.get("overseas_proxy", "http://127.0.0.1:10808"))
        env.setdefault("HTTP_PROXY", proxy)
        env.setdefault("HTTPS_PROXY", proxy)
        env.setdefault("ALL_PROXY", proxy)
        env.setdefault("NO_PROXY", "localhost,127.0.0.1,::1")
    return env


def should_use_proxy(config: dict[str, Any], *, no_proxy: bool = False) -> bool:
    if no_proxy:
        return False
    return str(config.get("proxy_mode", "auto")).lower() not in {"off", "none", "direct"}


def run_subprocess(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def read_usage_entries(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries[-limit:]

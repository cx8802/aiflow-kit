from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any


@dataclass
class CommandPreview:
    argv: list[str]
    display: str


def executable(name: str) -> str | None:
    return shutil.which(name)


def run_command(argv: list[str], *, cwd: Path | None = None, timeout: int | None = None) -> CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=timeout)


def preview_command(argv: list[str]) -> CommandPreview:
    return CommandPreview(argv=argv, display=subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv))


def wsl_base_command(*, distro: str = "", user: str = "", cwd: str = "") -> list[str]:
    argv = ["wsl"]
    if distro:
        argv.extend(["--distribution", distro])
    if user:
        argv.extend(["--user", user])
    if cwd:
        argv.extend(["--cd", cwd])
    return argv


def wsl_run_command(command: list[str], *, distro: str = "", user: str = "", cwd: str = "") -> list[str]:
    return [*wsl_base_command(distro=distro, user=user, cwd=cwd), "--", *command]


def wsl_path_command(path: str, *, to_windows: bool, distro: str = "") -> list[str]:
    flag = "-w" if to_windows else "-u"
    return [*wsl_base_command(distro=distro), "wslpath", flag, path]


def ssh_config_path(root: Path) -> Path:
    return root / ".aiflow" / "ssh.toml"


def ssh_local_path(root: Path) -> Path:
    return root / ".aiflow" / "ssh.local.toml"


def load_ssh_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"ssh": {}}
    with path.open("rb") as f:
        data = tomllib.load(f)
    data.setdefault("ssh", {})
    return data


def load_ssh(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return load_ssh_file(ssh_config_path(root)), load_ssh_file(ssh_local_path(root))


def save_ssh_file(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_ssh_toml(data), encoding="utf-8", newline="\n")


def dumps_ssh_toml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    profiles = data.get("ssh", {})
    for name in sorted(profiles):
        lines.append(f"[ssh.{name}]")
        for key, value in profiles[name].items():
            if value is None or value == "" or value == []:
                continue
            lines.append(f"{key} = {format_toml_value(value)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(format_toml_value(item) for item in value) + "]"
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def redact_ssh_profile(name: str, config_profile: dict[str, Any], local_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    local_profile = local_profile or {}
    result = {"name": name, **config_profile}
    for key in ["key_path", "password", "passphrase"]:
        if key in local_profile:
            result[f"{key}_local"] = "***"
    return result


def resolve_ssh_profile(root: Path, name: str) -> dict[str, Any] | None:
    config, local = load_ssh(root)
    config_profile = config.get("ssh", {}).get(name)
    if not config_profile:
        return None

    profile = dict(config_profile)
    profile.update(local.get("ssh", {}).get(name, {}))
    for value_key, env_key in [
        ("key_path", "key_path_env"),
        ("password", "password_env"),
        ("passphrase", "passphrase_env"),
    ]:
        env_name = profile.get(env_key)
        if env_name and os.environ.get(str(env_name)):
            profile[value_key] = os.environ[str(env_name)]
    return profile


def ssh_target(profile: dict[str, Any]) -> str:
    host = str(profile.get("host") or "")
    if not host:
        raise ValueError("ssh profile requires host")
    user = str(profile.get("user") or "")
    return f"{user}@{host}" if user else host


def ssh_command(profile: dict[str, Any], command: list[str], *, extra_args: list[str] | None = None) -> list[str]:
    argv = ["ssh"]
    port = int(profile.get("port") or 22)
    if port != 22:
        argv.extend(["-p", str(port)])
    key_path = profile.get("key_path")
    if key_path:
        argv.extend(["-i", str(key_path)])
    for option in profile.get("options", []) or []:
        argv.extend(["-o", str(option)])
    if extra_args:
        argv.extend(extra_args)
    argv.append(ssh_target(profile))
    if command:
        argv.append(_remote_command_text(command))
    return argv


def ssh_profile_json(name: str, config_profile: dict[str, Any], local_profile: dict[str, Any] | None = None) -> str:
    return json.dumps(redact_ssh_profile(name, config_profile, local_profile), indent=2, ensure_ascii=False)


def _remote_command_text(command: list[str]) -> str:
    if len(command) == 1:
        return command[0]
    return " ".join(shlex.quote(part) for part in command)

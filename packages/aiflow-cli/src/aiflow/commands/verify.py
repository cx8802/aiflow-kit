from __future__ import annotations

import json
import os
import subprocess
from argparse import Namespace
from pathlib import Path
from typing import Any

from ..core.config import load_config
from ..core.files import write_text_safely
from ..core.markdown import now_stamp
from ..core.paths import ensure_aiflow_dir, project_root


ORDER = ["lint", "typecheck", "test", "build"]


def run_verify(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    result = run_verification(
        root,
        root / ".aiflow",
        dry_run=args.dry_run,
        continue_on_error=args.continue_on_error,
        auto=getattr(args, "auto", False),
    )
    if not result["commands"]:
        print("No verification commands configured.")
    else:
        print("written: .aiflow/verify.md")
    return int(result["exit_code"])


def run_verification(
    root: Path,
    output_dir: Path,
    *,
    dry_run: bool = False,
    continue_on_error: bool = False,
    auto: bool = False,
) -> dict[str, Any]:
    config = load_config(root)
    commands = [(name, config.get("commands", {}).get(name, "")) for name in ORDER]
    if auto:
        commands = merge_auto_commands(root, commands)
    commands = [(name, command) for name, command in commands if command]

    generated_at = now_stamp()
    lines = ["# Verification", "", f"Generated at: {generated_at}", "", "## Commands", ""]
    payload: dict[str, Any] = {"ok": True, "generated_at": generated_at, "commands": [], "exit_code": 0}
    if not commands:
        lines.append("- No commands configured in `.aiflow/config.toml`.")
        write_text_safely(output_dir / "verify.md", "\n".join(lines) + "\n", force=True)
        write_json(output_dir / "verify.json", payload)
        return payload

    exit_code = 0
    results: list[str] = []
    for name, command in commands:
        lines.append(f"- {name}: `{command}`")
        command_result: dict[str, Any] = {
            "name": name,
            "command": command,
            "exit_code": 0,
            "required": True,
            "dry_run": dry_run,
        }
        if dry_run:
            results.append(f"- {name}: dry-run")
            payload["commands"].append(command_result)
            continue
        print(f"Running {name}: {command}")
        result = subprocess.run(command, cwd=root, shell=True, text=True, capture_output=True)
        command_result["exit_code"] = result.returncode
        results.append(f"- {name}: exit {result.returncode}")
        if result.stdout:
            command_result["stdout"] = result.stdout
            results.append(f"\n```text\n{result.stdout.strip()}\n```")
        if result.stderr:
            command_result["stderr"] = result.stderr
            results.append(f"\n```text\n{result.stderr.strip()}\n```")
        payload["commands"].append(command_result)
        if result.returncode != 0:
            exit_code = result.returncode
            payload["ok"] = False
            if not continue_on_error:
                break

    payload["exit_code"] = exit_code
    lines.extend(["", "## Results", "", *results])
    write_text_safely(output_dir / "verify.md", "\n".join(lines) + "\n", force=True)
    write_json(output_dir / "verify.json", payload)
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def merge_auto_commands(root: Path, commands: list[tuple[str, str]]) -> list[tuple[str, str]]:
    existing = {name: command for name, command in commands}
    for name, command in detect_verify_commands(root):
        if not existing.get(name):
            existing[name] = command
    return [(name, existing.get(name, "")) for name in ORDER]


def detect_verify_commands(root: Path) -> list[tuple[str, str]]:
    detected: dict[str, list[str]] = {name: [] for name in ORDER}
    for python_root in python_project_roots(root):
        if (python_root / "pyproject.toml").exists() or (python_root / "tests").exists():
            detected["test"].append(detect_python_test_command(root, python_root))
        if (python_root / "src").exists():
            detected["build"].append(f"python -m compileall {relative_command_path(root, python_root / 'src')}")
    detect_node_commands(root, detected)
    if (root / "go.mod").exists():
        detected["test"].append("go test ./...")
    if (root / "pom.xml").exists():
        detected["test"].append(maven_test_command(root))
    if has_gradle_project(root):
        detected["test"].append(gradle_test_command(root))
    return [(name, " && ".join(commands)) for name, commands in detected.items() if commands]


def python_project_roots(root: Path) -> list[Path]:
    roots: list[Path] = []
    if (root / "pyproject.toml").exists() or (root / "tests").exists() or (root / "src").exists():
        roots.append(root)
    packages_root = root / "packages"
    if packages_root.exists():
        for child in sorted(packages_root.iterdir(), key=lambda p: p.name.lower()):
            if child.is_dir() and ((child / "pyproject.toml").exists() or (child / "tests").exists() or (child / "src").exists()):
                roots.append(child)
    return roots


def detect_python_test_command(root: Path, python_root: Path) -> str:
    if has_pytest_config(python_root):
        path = relative_command_path(root, python_root)
        return "python -m pytest" if path == "." else f"python -m pytest {path}"
    return f"python -m unittest discover -s {relative_command_path(root, python_root / 'tests')}"


def relative_command_path(root: Path, path: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return str(path)
    text = relative.as_posix()
    return text or "."


def has_pytest_config(root: Path) -> bool:
    if (root / "pytest.ini").exists() or (root / "conftest.py").exists():
        return True
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return False
    try:
        import tomllib

        with pyproject.open("rb") as f:
            data = tomllib.load(f)
    except Exception:
        return False
    tool = data.get("tool", {}) if isinstance(data, dict) else {}
    return isinstance(tool, dict) and "pytest" in tool


def detect_node_commands(root: Path, detected: dict[str, list[str]]) -> None:
    package_json = root / "package.json"
    if not package_json.exists():
        return
    try:
        package = json.loads(package_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict):
        return

    runner = node_package_runner(root)
    script_map = {
        "lint": ["lint"],
        "typecheck": ["typecheck", "type-check"],
        "test": ["test", "check"],
        "build": ["build"],
    }
    for category, candidates in script_map.items():
        for script_name in candidates:
            if script_name in scripts:
                detected[category].append(node_script_command(runner, script_name))
                break


def node_package_runner(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    return "npm.cmd" if os.name == "nt" else "npm"


def node_script_command(runner: str, script_name: str) -> str:
    if runner in {"npm", "npm.cmd"}:
        return f"{runner} test" if script_name == "test" else f"{runner} run {script_name}"
    return f"{runner} {script_name}"


def maven_test_command(root: Path) -> str:
    wrapper = root / ("mvnw.cmd" if os.name == "nt" else "mvnw")
    return str(wrapper) + " test" if wrapper.exists() else "mvn test"


def has_gradle_project(root: Path) -> bool:
    return any((root / name).exists() for name in ["build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"])


def gradle_test_command(root: Path) -> str:
    wrapper = root / ("gradlew.bat" if os.name == "nt" else "gradlew")
    return str(wrapper) + " test" if wrapper.exists() else "gradle test"

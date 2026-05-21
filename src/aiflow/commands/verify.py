from __future__ import annotations

import json
import os
import subprocess
from argparse import Namespace
from pathlib import Path

from ..core.config import load_config
from ..core.files import write_text_safely
from ..core.markdown import now_stamp
from ..core.paths import ensure_aiflow_dir, project_root


ORDER = ["lint", "typecheck", "test", "build"]


def run_verify(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    config = load_config(root)
    commands = [(name, config.get("commands", {}).get(name, "")) for name in ORDER]
    if getattr(args, "auto", False):
        commands = merge_auto_commands(root, commands)
    commands = [(name, command) for name, command in commands if command]

    lines = ["# Verification", "", f"Generated at: {now_stamp()}", "", "## Commands", ""]
    if not commands:
        lines.append("- No commands configured in `.aiflow/config.toml`.")
        write_text_safely(root / ".aiflow" / "verify.md", "\n".join(lines) + "\n", force=True)
        print("No verification commands configured.")
        return 0

    exit_code = 0
    results: list[str] = []
    for name, command in commands:
        lines.append(f"- {name}: `{command}`")
        if args.dry_run:
            results.append(f"- {name}: dry-run")
            continue
        print(f"Running {name}: {command}")
        result = subprocess.run(command, cwd=root, shell=True, text=True, capture_output=True)
        results.append(f"- {name}: exit {result.returncode}")
        if result.stdout:
            results.append(f"\n```text\n{result.stdout.strip()}\n```")
        if result.stderr:
            results.append(f"\n```text\n{result.stderr.strip()}\n```")
        if result.returncode != 0:
            exit_code = result.returncode
            if not args.continue_on_error:
                break

    lines.extend(["", "## Results", "", *results])
    write_text_safely(root / ".aiflow" / "verify.md", "\n".join(lines) + "\n", force=True)
    print("written: .aiflow/verify.md")
    return exit_code


def merge_auto_commands(root: Path, commands: list[tuple[str, str]]) -> list[tuple[str, str]]:
    existing = {name: command for name, command in commands}
    for name, command in detect_verify_commands(root):
        if not existing.get(name):
            existing[name] = command
    return [(name, existing.get(name, "")) for name in ORDER]


def detect_verify_commands(root: Path) -> list[tuple[str, str]]:
    detected: dict[str, list[str]] = {name: [] for name in ORDER}
    if (root / "pyproject.toml").exists() or (root / "tests").exists():
        detected["test"].append(detect_python_test_command(root))
    if (root / "src").exists():
        detected["build"].append("python -m compileall src")
    detect_node_commands(root, detected)
    if (root / "go.mod").exists():
        detected["test"].append("go test ./...")
    if (root / "pom.xml").exists():
        detected["test"].append(maven_test_command(root))
    if has_gradle_project(root):
        detected["test"].append(gradle_test_command(root))
    return [(name, " && ".join(commands)) for name, commands in detected.items() if commands]


def detect_python_test_command(root: Path) -> str:
    if has_pytest_config(root):
        return "python -m pytest"
    return "python -m unittest discover -s tests"


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

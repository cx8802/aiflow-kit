from __future__ import annotations

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
    test_commands: list[str] = []
    if (root / "pyproject.toml").exists() or (root / "tests").exists():
        test_commands.append(detect_python_test_command(root))
    if (root / "package.json").exists():
        test_commands.append("npm.cmd test")
    if (root / "go.mod").exists():
        test_commands.append("go test ./...")
    if (root / "pom.xml").exists():
        test_commands.append("mvn test")
    return [("test", " && ".join(test_commands))] if test_commands else []


def detect_python_test_command(root: Path) -> str:
    if (root / "pytest.ini").exists() or (root / "conftest.py").exists():
        return "python -m pytest"
    return "python -m unittest discover -s tests"

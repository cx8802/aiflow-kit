from __future__ import annotations

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any

from ..core.agents import find_task_file
from ..core.claude_agent import (
    SDK_PACKAGE,
    claude_code_command,
    claude_agent_config,
    command_env,
    default_context_files,
    ensure_package_json,
    make_run_id,
    node_command,
    npm_command,
    package_dir,
    read_usage_entries,
    resolve_model,
    runner_path,
    runs_dir,
    sdk_installed,
    sessions_dir,
    should_use_proxy,
    usage_file,
    write_json,
)
from ..core.paths import ensure_aiflow_dir, project_root


def configure_claude_agent_parser(sub) -> None:
    parser = sub.add_parser("claude-agent", help="Use aiflow-kit Claude Agent SDK worker")
    agent_sub = parser.add_subparsers(dest="claude_agent_command", required=True)

    install = agent_sub.add_parser("install", help="Install Claude Agent SDK into aiflow-kit tools")
    install.add_argument("--dry-run", action="store_true", help="Print commands without running npm")
    install.add_argument("--no-proxy", action="store_true", help="Do not set 10808 proxy for npm install")
    install.set_defaults(func=run_claude_agent)

    doctor = agent_sub.add_parser("doctor", help="Check Claude Agent SDK configuration")
    doctor.set_defaults(func=run_claude_agent)

    run = agent_sub.add_parser("run", help="Run a generic Claude Agent SDK task")
    add_run_args(run)
    run.set_defaults(func=run_claude_agent)

    explore = agent_sub.add_parser("explore", help="Run a read-only code exploration task")
    add_run_args(explore)
    explore.set_defaults(func=run_claude_agent)

    review = agent_sub.add_parser("review-diff", help="Review the current git diff with Claude Agent SDK")
    add_run_args(review, prompt_required=False)
    review.set_defaults(func=run_claude_agent)

    compact = agent_sub.add_parser("compact", help="Generate compact context with Claude Agent SDK")
    add_run_args(compact, prompt_required=False)
    compact.set_defaults(func=run_claude_agent)

    usage = agent_sub.add_parser("usage", help="Show recent Claude Agent SDK usage records")
    usage.add_argument("--limit", type=int, default=20, help="Maximum usage records to show")
    usage.set_defaults(func=run_claude_agent)


def add_run_args(parser, *, prompt_required: bool = True) -> None:
    parser.add_argument("prompt", nargs="+" if prompt_required else "*", help="Task prompt")
    parser.add_argument("--model", default=None, help="Model alias or full model id")
    parser.add_argument("--allow-edit", action="store_true", help="Allow Edit/Write tools for this run")
    parser.add_argument("--edit-scope", action="append", default=[], help="Allowed file or directory path for --allow-edit")
    parser.add_argument("--task-id", default="", help="Bind this run to a .aiflow/agents task id")
    parser.add_argument("--verify-after", action="store_true", help="Run aiflow verify --auto --continue-on-error after a successful SDK run")
    parser.add_argument("--dry-run", action="store_true", help="Write and print input without invoking Node")
    parser.add_argument("--force", action="store_true", help="Run even when claude_agent.enabled is false")
    parser.add_argument("--no-proxy", action="store_true", help="Do not set 10808 proxy for SDK call")
    parser.add_argument("--max-turns", type=int, default=None, help="Override claude_agent.max_turns")


def run_claude_agent(args: Namespace) -> int:
    command = args.claude_agent_command
    if command == "install":
        return claude_agent_install(args)
    if command == "doctor":
        return claude_agent_doctor(args)
    if command == "usage":
        return claude_agent_usage(args)
    return claude_agent_run(args)


def claude_agent_install(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    config = claude_agent_config(root)
    npm = npm_command()
    if not npm:
        print("npm not found. Install Node.js/npm first.")
        return 1

    target = package_dir(root, config)
    command = [npm, "install", "--prefix", str(target), SDK_PACKAGE]
    print(f"claude agent tools: {target}")
    print(" ".join(quote(part) for part in command))
    if args.dry_run:
        return 0

    ensure_package_json(target)
    env = command_env(root, config, use_proxy=should_use_proxy(config, no_proxy=args.no_proxy))
    result = subprocess.run(command, cwd=root, env=env, text=True)
    return result.returncode


def claude_agent_doctor(args: Namespace) -> int:
    root = project_root()
    config = claude_agent_config(root)
    node = node_command()
    npm = npm_command()
    api_key_env = str(config.get("api_key_env", "ANTHROPIC_API_KEY"))
    base_url_env = str(config.get("base_url_env", "ANTHROPIC_BASE_URL"))
    runner = runner_path(root, config)
    target = package_dir(root, config)

    env = command_env(root, config, use_proxy=False)
    rows = [
        ("enabled", "ok" if config.get("enabled") else "disabled", str(config.get("enabled", False))),
        ("node", "ok" if node else "missing", node or ""),
        ("npm", "ok" if npm else "missing", npm or ""),
        ("sdk package", "ok" if sdk_installed(root, config) else "missing", str(target)),
        ("runner", "ok" if runner.exists() else "missing", str(runner)),
        ("api key env", "ok" if api_key_env and api_key_env in env else "missing", api_key_env),
        ("base url env", "optional", base_url_env),
    ]
    print("# Claude Agent Doctor")
    print("")
    print("| Check | Status | Detail |")
    print("| --- | --- | --- |")
    for name, status, detail in rows:
        print(f"| {name} | {status} | `{detail}` |")
    return 0


def claude_agent_run(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    config = claude_agent_config(root)
    command = args.claude_agent_command

    if not config.get("enabled", False) and not args.force and not args.dry_run:
        print("claude_agent.enabled is false. Enable it or pass --force.")
        return 2

    model, error = resolve_model(config, args.model)
    if error:
        print(error)
        return 2
    if args.edit_scope and not args.allow_edit:
        print("--edit-scope requires --allow-edit")
        return 2

    env = command_env(root, config, use_proxy=should_use_proxy(config, no_proxy=args.no_proxy))
    if not args.dry_run:
        api_key_env = str(config.get("api_key_env", "ANTHROPIC_API_KEY"))
        if api_key_env and api_key_env not in env:
            print(f"Missing API key environment variable: {api_key_env}")
            return 2
        if not sdk_installed(root, config):
            print("Claude Agent SDK is not installed. Run: aiflow claude-agent install")
            return 2
        node = node_command()
        if not node:
            print("node not found. Install Node.js first.")
            return 1
        if not runner_path(root, config).exists():
            print(f"Runner not found: {runner_path(root, config)}")
            return 1

    run_dir = runs_dir(root, config) / make_run_id(command)
    prompt = build_prompt(root, command, " ".join(args.prompt), args)
    input_data = build_input(root, config, command, prompt, model, args, run_dir)

    if args.dry_run:
        print(json.dumps(input_data, ensure_ascii=False, indent=2))
        return 0

    write_json(run_dir / "input.json", input_data)
    node = node_command()
    assert node is not None
    try:
        result = subprocess.run(
            [node, str(runner_path(root, config)), str(run_dir / "input.json")],
            cwd=root,
            env=env,
            text=True,
            timeout=int(input_data.get("timeoutSeconds", 300)),
        )
    except subprocess.TimeoutExpired:
        print(f"Claude Agent SDK run timed out after {input_data.get('timeoutSeconds', 300)} seconds")
        return 124
    if result.returncode == 0 and args.verify_after:
        verify = subprocess.run(
            [sys.executable, "-m", "aiflow", "verify", "--auto", "--continue-on-error"],
            cwd=root,
            text=True,
        )
        return verify.returncode
    return result.returncode


def build_prompt(root: Path, command: str, prompt: str, args: Namespace) -> str:
    if command == "explore":
        base = f"Read-only exploration task: {prompt}\nReturn concise findings, risks, and relevant files."
    elif command == "review-diff":
        diff = git_diff(root)
        user_prompt = prompt or "Review the current git diff for bugs, risks, missing tests, and unsafe changes."
        base = f"{user_prompt}\n\n# Git Diff\n\n```diff\n{diff}\n```"
    elif command == "compact":
        base = prompt or "Create a concise compact context from the provided aiflow context files. Preserve commands, risks, current plan, and memory."
    else:
        base = prompt
    return append_run_constraints(root, base, args)


def append_run_constraints(root: Path, prompt: str, args: Namespace) -> str:
    sections = [prompt.rstrip()]
    task_id = str(getattr(args, "task_id", "") or "").strip()
    if task_id:
        sections.extend(["", "## Aiflow Task Binding", "", f"- Task id: `{task_id}`"])
        task_file = find_task_file(root, task_id)
        if task_file:
            sections.extend(
                [
                    f"- Task file: `{task_file.relative_to(root).as_posix()}`",
                    "",
                    "```text",
                    task_file.read_text(encoding="utf-8")[:20_000],
                    "```",
                ]
            )

    edit_scope = normalized_edit_scope(args)
    if edit_scope:
        sections.extend(["", "## Edit Scope", ""])
        sections.extend(f"- `{scope}`" for scope in edit_scope)
        sections.append("")
        sections.append("Do not edit files outside the listed scope. If the task requires broader edits, stop and report the blocker.")
    elif getattr(args, "allow_edit", False):
        sections.extend(
            [
                "",
                "## Edit Scope",
                "",
                "No explicit edit scope was provided. Keep edits to the minimum files directly required by the task and report any broader need.",
            ]
        )

    if getattr(args, "verify_after", False):
        sections.extend(
            [
                "",
                "## Post-run Verification",
                "",
                "After implementation, the orchestrator will run `aiflow verify --auto --continue-on-error`.",
                "Return a concise patch summary and any verification risks.",
            ]
        )
    return "\n".join(sections).rstrip() + "\n"


def build_input(
    root: Path,
    config: dict[str, Any],
    command: str,
    prompt: str,
    model: str,
    args: Namespace,
    run_dir: Path,
) -> dict[str, Any]:
    allow_edit = bool(args.allow_edit)
    allowed_tools = list(config.get("allowed_tools", ["Read", "Glob", "Grep"]))
    disallowed_tools = list(config.get("disallowed_tools", ["Bash", "Edit", "Write"]))
    if allow_edit:
        for tool in ["Edit", "Write"]:
            if tool not in allowed_tools:
                allowed_tools.append(tool)
        disallowed_tools = [tool for tool in disallowed_tools if tool not in {"Edit", "Write"}]

    write_result_to = None
    if command == "compact":
        write_result_to = str(root / ".aiflow" / "context.compact.md")

    return {
        "cwd": str(root),
        "task": command,
        "taskId": str(getattr(args, "task_id", "") or ""),
        "prompt": prompt,
        "model": model,
        "packageDir": str(package_dir(root, config)),
        "claudeCodeExecutable": claude_code_command(),
        "outputDir": str(run_dir),
        "usageFile": str(usage_file(root, config)),
        "sessionsDir": str(sessions_dir(root, config)),
        "contextFiles": default_context_files(root),
        "permissionMode": str(config.get("permission_mode", "dontAsk")),
        "allowedTools": allowed_tools,
        "disallowedTools": disallowed_tools,
        "editScope": normalized_edit_scope(args),
        "maxTurns": args.max_turns or int(config.get("max_turns", 8)),
        "maxBudgetUsd": float(config.get("max_budget_usd", 0.2)),
        "timeoutSeconds": int(config.get("timeout_seconds", 300)),
        "postRunVerifyCommand": "aiflow verify --auto --continue-on-error" if getattr(args, "verify_after", False) else "",
        "writeResultTo": write_result_to,
    }


def normalized_edit_scope(args: Namespace) -> list[str]:
    raw_scope = getattr(args, "edit_scope", []) or []
    scope: list[str] = []
    seen: set[str] = set()
    for item in raw_scope:
        value = str(item).replace("\\", "/").strip().strip("/")
        if value and value not in seen:
            scope.append(value)
            seen.add(value)
    return scope


def git_diff(root: Path) -> str:
    result = subprocess.run(["git", "diff", "--", "."], cwd=root, text=True, capture_output=True)
    if result.returncode != 0:
        return result.stderr.strip()
    diff = result.stdout
    max_chars = 120_000
    if len(diff) > max_chars:
        return diff[:max_chars] + "\n... diff truncated ..."
    return diff or "No git diff."


def claude_agent_usage(args: Namespace) -> int:
    root = project_root()
    config = claude_agent_config(root)
    entries = read_usage_entries(usage_file(root, config), limit=max(args.limit, 0))
    if not entries:
        print("no claude agent usage records")
        return 0
    print(json.dumps(entries, ensure_ascii=False, indent=2))
    return 0


def quote(value: str) -> str:
    return f'"{value}"' if " " in value else value

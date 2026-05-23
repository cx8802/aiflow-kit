from __future__ import annotations

import os
import shutil
import subprocess
from argparse import Namespace
from pathlib import Path

from ..core.environment import aiflow_kit_root
from ..core.paths import ensure_aiflow_dir


def configure_frontend_parser(sub) -> None:
    frontend = sub.add_parser("frontend", help="Install and verify frontend design tooling")
    frontend_sub = frontend.add_subparsers(dest="frontend_command", required=True)

    install = frontend_sub.add_parser("install", help="Install aiflow-kit Playwright tooling")
    install.add_argument("--dry-run", action="store_true", help="Print commands without running them")
    install.add_argument("--skip-browsers", action="store_true", help="Install npm package only")
    install.add_argument("--no-proxy", action="store_true", help="Do not set 10808 proxy for browser download")
    install.set_defaults(func=run_frontend)


def run_frontend(args: Namespace) -> int:
    if args.frontend_command == "install":
        return frontend_install(args)
    raise ValueError(f"Unknown frontend command: {args.frontend_command}")


def frontend_install(args: Namespace) -> int:
    root = aiflow_kit_root()
    ensure_aiflow_dir(root)
    tools_root = root / ".tools"
    frontend_tools = tools_root / "frontend-tools"
    browsers_path = tools_root / "ms-playwright"
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        print("npm not found. Install Node.js/npm first.")
        return 1

    commands = [
        ([npm, "install", "--prefix", str(frontend_tools), "@playwright/test"], False),
    ]
    playwright = playwright_bin(frontend_tools)
    if not args.skip_browsers:
        commands.append(([str(playwright), "install", "chromium"], True))

    print(f"frontend tools: {frontend_tools}")
    print(f"playwright browsers: {browsers_path}")
    if args.dry_run:
        print("would ensure aiflow-kit .gitignore entries: .tools/, .cache/")
    else:
        frontend_tools.mkdir(parents=True, exist_ok=True)
        browsers_path.mkdir(parents=True, exist_ok=True)
        ensure_gitignore_entries(root, [".tools/", ".cache/"])

    base_env = os.environ.copy()
    base_env["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)

    for command, use_overseas_proxy in commands:
        print(" ".join(quote(part) for part in command))
        if args.dry_run:
            continue
        env = command_env(base_env, use_overseas_proxy and not args.no_proxy)
        result = subprocess.run(command, cwd=root, env=env, text=True)
        if result.returncode != 0:
            return result.returncode
    return 0


def command_env(base_env: dict[str, str], use_proxy: bool) -> dict[str, str]:
    env = dict(base_env)
    if use_proxy:
        proxy = env.get("AIFLOW_PROXY_URL", "http://127.0.0.1:10808")
        env.setdefault("HTTP_PROXY", proxy)
        env.setdefault("HTTPS_PROXY", proxy)
        env.setdefault("ALL_PROXY", proxy)
        env.setdefault("NO_PROXY", "localhost,127.0.0.1,::1")
    return env


def playwright_bin(frontend_tools: Path) -> Path:
    if os.name == "nt":
        return frontend_tools / "node_modules" / ".bin" / "playwright.cmd"
    return frontend_tools / "node_modules" / ".bin" / "playwright"


def ensure_gitignore_entries(root: Path, entries: list[str]) -> None:
    gitignore = root / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        lines = content.splitlines()
    else:
        content = ""
        lines = []

    existing = {line.strip() for line in lines}
    missing = [entry for entry in entries if entry not in existing]
    if not missing:
        return

    output = content
    if output and not output.endswith(("\n", "\r\n")):
        output += "\n"
    if output:
        output += "\n"
    output += "# aiflow project-local tools\n"
    output += "\n".join(missing)
    output += "\n"
    gitignore.write_text(output, encoding="utf-8", newline="\n")


def quote(value: str) -> str:
    return f'"{value}"' if " " in value else value

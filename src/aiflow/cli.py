from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .commands.context import run_context
from .commands.db import configure_db_parser
from .commands.doctor import run_doctor
from .commands.init import run_init
from .commands.install_skills import run_install_skills
from .commands.plan import run_plan
from .commands.review import run_review
from .commands.verify import run_verify


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aiflow",
        description="AI coding workflow CLI for project context, skills, verification, and release review.",
    )
    parser.add_argument("--version", action="version", version=f"aiflow {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize AGENTS.md, CLAUDE.md, and .aiflow/config.toml")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing generated files")
    p_init.add_argument("--no-claude", action="store_true", help="Do not generate CLAUDE.md")
    p_init.add_argument("--no-codex", action="store_true", help="Do not generate AGENTS.md")
    p_init.add_argument("--no-context", action="store_true", help="Do not generate .aiflow/context.md")
    p_init.set_defaults(func=run_init)

    p_doctor = sub.add_parser("doctor", help="Check local environment and project configuration")
    p_doctor.add_argument("--no-write", action="store_true", help="Do not write .aiflow/doctor.md")
    p_doctor.set_defaults(func=run_doctor)

    p_context = sub.add_parser("context", help="Generate .aiflow/context.md")
    p_context.add_argument("--output", type=Path, default=None, help="Optional output path")
    p_context.set_defaults(func=run_context)

    p_plan = sub.add_parser("plan", help="Generate .aiflow/plan.md")
    p_plan.add_argument("goal", nargs="*", help="Optional goal text")
    p_plan.add_argument("--force", action="store_true", help="Overwrite existing plan")
    p_plan.set_defaults(func=run_plan)

    p_review = sub.add_parser("review", help="Generate .aiflow/review.md from git diff")
    p_review.add_argument("--output", type=Path, default=None, help="Optional output path")
    p_review.set_defaults(func=run_review)

    p_verify = sub.add_parser("verify", help="Run configured verification commands")
    p_verify.add_argument("--dry-run", action="store_true", help="Only print commands")
    p_verify.add_argument("--continue-on-error", action="store_true", help="Continue after failures")
    p_verify.set_defaults(func=run_verify)

    p_install = sub.add_parser("install-skills", help="Install bundled skills")
    p_install.add_argument(
        "--target",
        choices=["codex-repo", "codex-user", "claude-user", "claude-plugin", "codex-plugin", "all"],
        default="codex-repo",
        help="Install target. Default: codex-repo",
    )
    p_install.add_argument("--output", type=Path, default=None, help="Plugin output directory")
    p_install.add_argument("--force", action="store_true", help="Overwrite existing skills")
    p_install.add_argument("--confirm-global", action="store_true", help="Required for user-level installs")
    p_install.add_argument("--allow-global", action="store_true", help="Allow generic bundled skills to be installed globally")
    p_install.set_defaults(func=run_install_skills)

    configure_db_parser(sub)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)

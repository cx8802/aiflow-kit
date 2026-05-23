from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .commands.agents import configure_agents_parser
from .commands.browser import configure_browser_parser
from .commands.claude_agent import configure_claude_agent_parser
from .commands.codegraph import configure_codegraph_parser
from .commands.config import configure_config_parser
from .commands.context import run_context
from .commands.db import configure_db_parser
from .commands.doctor import run_doctor
from .commands.env import configure_env_parser
from .commands.forge import configure_forge_parser
from .commands.frontend import configure_frontend_parser
from .commands.graphify import configure_graphify_parser
from .commands.init import run_init
from .commands.install_skills import run_install_skills
from .commands.memory import configure_memory_parser
from .commands.nacos import configure_nacos_parser
from .commands.plan import run_plan
from .commands.review import run_review
from .commands.ssh import configure_ssh_parser
from .commands.verify import run_verify
from .commands.workflow import run_workflow
from .commands.wsl import configure_wsl_parser


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
    p_context.add_argument("--compact", action="store_true", help="Also generate .aiflow/context.compact.md")
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
    p_verify.add_argument("--auto", action="store_true", help="Infer missing verification commands from project files")
    p_verify.set_defaults(func=run_verify)

    p_workflow = sub.add_parser("workflow", help="Run the standard aiflow context, plan, verify, and review workflow")
    p_workflow.add_argument("goal", nargs="*", help="Optional goal text for .aiflow/plan.md")
    p_workflow.add_argument("--no-compact", action="store_true", help="Only refresh .aiflow/context.md")
    p_workflow.add_argument("--skip-plan", action="store_true", help="Do not generate .aiflow/plan.md")
    p_workflow.add_argument("--force-plan", action="store_true", help="Overwrite existing .aiflow/plan.md")
    p_workflow.add_argument("--verify", action="store_true", help="Run aiflow verify --auto")
    p_workflow.add_argument("--review", action="store_true", help="Run aiflow review")
    p_workflow.add_argument("--check", action="store_true", help="Run verify --auto --continue-on-error, then review")
    p_workflow.add_argument("--no-auto-verify", action="store_true", help="Use only configured verification commands")
    p_workflow.add_argument("--continue-on-error", action="store_true", help="Continue verification after failures")
    p_workflow.add_argument("--dry-run", action="store_true", help="Print workflow steps without writing files")
    p_workflow.set_defaults(func=run_workflow)

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

    configure_agents_parser(sub)
    configure_browser_parser(sub)
    configure_claude_agent_parser(sub)
    configure_codegraph_parser(sub)
    configure_config_parser(sub)
    configure_db_parser(sub)
    configure_env_parser(sub)
    configure_forge_parser(sub)
    configure_frontend_parser(sub)
    configure_graphify_parser(sub)
    configure_memory_parser(sub)
    configure_nacos_parser(sub)
    configure_ssh_parser(sub)
    configure_wsl_parser(sub)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)

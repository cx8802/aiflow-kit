from __future__ import annotations

from argparse import Namespace

from ..core.agents import (
    agents_root,
    default_handoff,
    default_status,
    plan_handoff,
    plan_status,
    plan_tasks,
    roles_toml,
    summarize_agents,
    task_markdown,
    tasks_root,
    update_task_state,
)
from ..core.files import write_text_safely
from ..core.paths import ensure_aiflow_dir, project_root


def configure_agents_parser(sub) -> None:
    agents = sub.add_parser("agents", help="Manage project-level multi-agent workflow files")
    agents_sub = agents.add_subparsers(dest="agents_command", required=True)

    init = agents_sub.add_parser("init", help="Initialize .aiflow/agents workspace")
    init.add_argument("--force", action="store_true", help="Overwrite existing generated files")
    init.set_defaults(func=run_agents)

    plan = agents_sub.add_parser("plan", help="Create a project-level multi-agent task queue")
    plan.add_argument("goal", nargs="*", help="Goal to split across agents")
    plan.add_argument("--force", action="store_true", help="Overwrite existing generated task files")
    plan.set_defaults(func=run_agents)

    status = agents_sub.add_parser("status", help="Show multi-agent workspace status")
    status.set_defaults(func=run_agents)

    handoff = agents_sub.add_parser("handoff", help="Create or refresh the multi-agent handoff file")
    handoff.add_argument("goal", nargs="*", help="Optional goal text")
    handoff.add_argument("--force", action="store_true", help="Overwrite existing handoff")
    handoff.set_defaults(func=run_agents)

    for command, state, help_text in [
        ("start", "in_progress", "Mark a task as in progress"),
        ("done", "done", "Mark a task as done"),
        ("block", "blocked", "Mark a task as blocked"),
    ]:
        state_cmd = agents_sub.add_parser(command, help=help_text)
        state_cmd.add_argument("task_id", help="Task id or unique task id fragment")
        state_cmd.add_argument("note", nargs="*", help="Optional note")
        state_cmd.set_defaults(func=run_agents, agent_state=state)


def run_agents(args: Namespace) -> int:
    command = args.agents_command
    if command == "init":
        return agents_init(args)
    if command == "plan":
        return agents_plan(args)
    if command == "status":
        return agents_status(args)
    if command == "handoff":
        return agents_handoff(args)
    if command in {"start", "done", "block"}:
        return agents_set_state(args)
    raise ValueError(f"Unknown agents command: {command}")


def agents_init(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    base = agents_root(root)
    tasks_root(root).mkdir(parents=True, exist_ok=True)

    reports = [
        write_text_safely(base / "roles.toml", roles_toml(), force=args.force),
        write_text_safely(base / "status.md", default_status(), force=args.force),
        write_text_safely(base / "handoff.md", default_handoff(), force=args.force),
    ]
    for path, status in reports:
        print(f"{status}: {path.relative_to(root)}")
    print(f"ready: {(base / 'tasks').relative_to(root)}")
    return 0


def agents_plan(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    goal = " ".join(args.goal).strip() or "<describe goal>"
    base = agents_root(root)
    task_dir = tasks_root(root)
    task_dir.mkdir(parents=True, exist_ok=True)

    reports = [
        write_text_safely(base / "roles.toml", roles_toml(), force=args.force),
    ]
    tasks = plan_tasks(goal)
    for task in tasks:
        reports.append(
            write_text_safely(task_dir / f"{task.task_id}.md", task_markdown(task, goal), force=args.force)
        )
    reports.extend(
        [
            write_text_safely(base / "status.md", plan_status(goal, tasks), force=args.force),
            write_text_safely(base / "handoff.md", plan_handoff(goal, tasks), force=args.force),
        ]
    )

    for path, status in reports:
        print(f"{status}: {path.relative_to(root)}")
    return 0


def agents_status(args: Namespace) -> int:
    root = project_root()
    for line in summarize_agents(root):
        print(line)
    return 0


def agents_handoff(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    goal = " ".join(args.goal).strip() or "<describe goal>"
    base = agents_root(root)
    base.mkdir(parents=True, exist_ok=True)
    path, status = write_text_safely(base / "handoff.md", default_handoff(goal), force=args.force)
    print(f"{status}: {path.relative_to(root)}")
    return 0


def agents_set_state(args: Namespace) -> int:
    root = project_root()
    note = " ".join(args.note).strip()
    try:
        path = update_task_state(root, args.task_id, args.agent_state, note)
    except FileNotFoundError as exc:
        print(str(exc))
        return 2
    print(f"updated: {path.relative_to(root)} -> {args.agent_state}")
    return 0

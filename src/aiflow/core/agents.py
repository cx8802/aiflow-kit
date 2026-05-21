from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from re import sub

from .markdown import now_stamp


AGENT_ROLES = [
    {
        "name": "orchestrator",
        "description": "Split goals, assign bounded work, track status, and merge handoffs.",
        "owns": "planning, task boundaries, final integration",
    },
    {
        "name": "explorer",
        "description": "Read code and answer specific architecture, impact, and risk questions.",
        "owns": "read-only analysis and references",
    },
    {
        "name": "worker",
        "description": "Implement scoped changes in explicitly assigned files or modules.",
        "owns": "bounded code changes and local tests",
    },
    {
        "name": "reviewer",
        "description": "Review diffs, verification results, risks, and release readiness.",
        "owns": "findings, verification gaps, release summary",
    },
]


@dataclass
class AgentTask:
    task_id: str
    role: str
    title: str
    objective: str
    write_scope: str


def agents_root(root: Path) -> Path:
    return root / ".aiflow" / "agents"


def tasks_root(root: Path) -> Path:
    return agents_root(root) / "tasks"


def roles_toml() -> str:
    lines = [
        "# aiflow multi-agent roles",
        "# Generic role definitions are safe to share. Project-specific tasks stay in .aiflow/agents/tasks/.",
        "",
    ]
    for role in AGENT_ROLES:
        lines.extend(
            [
                "[[roles]]",
                f"name = {toml_string(role['name'])}",
                f"description = {toml_string(role['description'])}",
                f"owns = {toml_string(role['owns'])}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def default_status(goal: str = "") -> str:
    title = goal or "<describe goal>"
    return f"""# Multi-Agent Status

## Goal

{title}

## Generated At

{now_stamp()}

## State

- orchestrator: pending
- explorer: pending
- worker: pending
- reviewer: pending

## Active Tasks

- None

## Notes

- Keep concrete project facts, credentials, and task outputs inside this directory.
- Do not copy project-specific task details into global Codex or Claude rules.
"""


def default_handoff(goal: str = "") -> str:
    title = goal or "<describe goal>"
    return f"""# Multi-Agent Handoff

## Goal

{title}

## Summary

- Pending.

## Completed Tasks

- None

## Verification

- Pending.

## Risks

- Pending.

## Next Steps

- Pending.
"""


def plan_tasks(goal: str) -> list[AgentTask]:
    clean_goal = goal.strip() or "<describe goal>"
    slug = slugify(clean_goal)
    return [
        AgentTask(
            task_id=f"001-explore-{slug}",
            role="explorer",
            title="Explore impact and constraints",
            objective=f"Read the repository context for: {clean_goal}. Identify affected modules, commands, risks, and unknowns.",
            write_scope="Read-only. Do not edit files.",
        ),
        AgentTask(
            task_id=f"002-implement-{slug}",
            role="worker",
            title="Implement scoped changes",
            objective=f"Implement the agreed smallest useful change for: {clean_goal}. Keep edits within assigned files.",
            write_scope="Only files explicitly assigned by the orchestrator.",
        ),
        AgentTask(
            task_id=f"003-verify-{slug}",
            role="worker",
            title="Run focused verification",
            objective=f"Run or improve focused tests for: {clean_goal}. Record exact commands and results.",
            write_scope="Test files and verification notes assigned by the orchestrator.",
        ),
        AgentTask(
            task_id=f"004-review-{slug}",
            role="reviewer",
            title="Review and release handoff",
            objective=f"Review implementation, risks, tests, and release readiness for: {clean_goal}.",
            write_scope="Review notes only unless the orchestrator assigns fixes.",
        ),
    ]


def task_markdown(task: AgentTask, goal: str) -> str:
    return f"""# {task.task_id}

## Role

{task.role}

## Title

{task.title}

## Goal

{goal}

## Objective

{task.objective}

## Write Scope

{task.write_scope}

## Inputs

- Read `AGENTS.md` and `.aiflow/context.md` before starting.
- Check `.aiflow/agents/status.md` for current state.
- Coordinate through `.aiflow/agents/handoff.md` when work is complete.

## Output Contract

- Status: pending | in_progress | blocked | done
- Files changed:
- Commands run:
- Findings:
- Risks:
- Handoff:
"""


def plan_status(goal: str, tasks: list[AgentTask]) -> str:
    lines = [
        "# Multi-Agent Status",
        "",
        "## Goal",
        "",
        goal,
        "",
        "## Generated At",
        "",
        now_stamp(),
        "",
        "## State",
        "",
    ]
    for task in tasks:
        lines.append(f"- {task.task_id}: pending ({task.role})")
    lines.extend(
        [
            "",
            "## Active Tasks",
            "",
            "- None",
            "",
            "## Notes",
            "",
            "- Orchestrator owns task boundaries and final integration.",
            "- Workers must not revert unrelated edits or edits made by other agents.",
            "- Store project-specific task outputs here, not in global Skills.",
            "",
        ]
    )
    return "\n".join(lines)


def plan_handoff(goal: str, tasks: list[AgentTask]) -> str:
    return f"""# Multi-Agent Handoff

## Goal

{goal}

## Task Queue

{''.join(f'- `{task.task_id}`: {task.title} ({task.role})\n' for task in tasks)}
## Integration Notes

- Pending.

## Verification

- Pending.

## Risks

- Pending.

## Final Summary

- Pending.
"""


def summarize_agents(root: Path) -> list[str]:
    base = agents_root(root)
    if not base.exists():
        return ["Multi-agent workspace is not initialized. Run `aiflow agents init`."]
    lines = [f"agents: {base}"]
    role_path = base / "roles.toml"
    status_path = base / "status.md"
    handoff_path = base / "handoff.md"
    lines.append(f"roles: {'present' if role_path.exists() else 'missing'}")
    lines.append(f"status: {'present' if status_path.exists() else 'missing'}")
    lines.append(f"handoff: {'present' if handoff_path.exists() else 'missing'}")
    task_files = sorted((base / "tasks").glob("*.md")) if (base / "tasks").exists() else []
    lines.append(f"tasks: {len(task_files)}")
    for task in task_files:
        lines.append(f"- {task.name}")
    return lines


def find_task_file(root: Path, task_id: str) -> Path | None:
    task_dir = tasks_root(root)
    if not task_dir.exists():
        return None
    normalized = task_id[:-3] if task_id.endswith(".md") else task_id
    direct = task_dir / f"{normalized}.md"
    if direct.exists():
        return direct
    matches = sorted(task_dir.glob(f"*{normalized}*.md"))
    return matches[0] if len(matches) == 1 else None


def update_task_state(root: Path, task_id: str, state: str, note: str = "") -> Path:
    task_file = find_task_file(root, task_id)
    if not task_file:
        raise FileNotFoundError(f"Task not found: {task_id}")
    content = task_file.read_text(encoding="utf-8")
    block = task_state_block(state, note)
    marker = "## Agent State"
    if marker in content:
        before = content.split(marker, 1)[0].rstrip()
        after_section = content.split(marker, 1)[1]
        rest = ""
        if "\n## " in after_section:
            rest = "\n## " + after_section.split("\n## ", 1)[1].lstrip()
        content = f"{before}\n\n{block}{rest}"
    else:
        content = f"{content.rstrip()}\n\n{block}"
    task_file.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")
    update_status_file(root, task_file.stem, state, note)
    return task_file


def task_state_block(state: str, note: str = "") -> str:
    lines = [
        "## Agent State",
        "",
        f"- Status: {state}",
        f"- Updated At: {now_stamp()}",
    ]
    if note:
        lines.append(f"- Note: {note}")
    lines.append("")
    return "\n".join(lines)


def update_status_file(root: Path, task_id: str, state: str, note: str = "") -> None:
    status_path = agents_root(root) / "status.md"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    if not status_path.exists():
        status_path.write_text(default_status(), encoding="utf-8", newline="\n")
    lines = status_path.read_text(encoding="utf-8").splitlines()
    updated: list[str] = []
    found = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"- {task_id}:"):
            suffix = f" - {note}" if note else ""
            updated.append(f"- {task_id}: {state}{suffix}")
            found = True
        else:
            updated.append(line)
    if not found:
        updated.extend(["", f"- {task_id}: {state}" + (f" - {note}" if note else "")])
    status_path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8", newline="\n")


def slugify(text: str) -> str:
    slug = sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug[:40].strip("-") or "goal"


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

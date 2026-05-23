from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .files import write_text_safely
from .markdown import now_stamp
from .paths import ensure_aiflow_dir
from .project_scan import build_context_report
from .resources import read_template


STAGES = ["context", "spec", "plan", "implementation", "verify", "review", "finish"]


@dataclass
class WorkflowRun:
    root: Path
    run_id: str

    @property
    def path(self) -> Path:
        return runs_dir(self.root) / self.run_id


def runs_dir(root: Path) -> Path:
    return root / ".aiflow" / "runs"


def current_run_path(root: Path) -> Path:
    return runs_dir(root) / "current"


def create_run(root: Path, goal: str) -> WorkflowRun:
    ensure_aiflow_dir(root)
    base = runs_dir(root)
    base.mkdir(parents=True, exist_ok=True)
    run = WorkflowRun(root=root, run_id=unique_run_id(base, goal))
    run.path.mkdir(parents=True, exist_ok=False)

    write_run_text(run, "input.md", f"# Workflow Input\n\n{goal}\n")
    context = build_context_report(root)
    write_run_text(run, "context.md", context)
    write_run_text(run, "spec.md", build_spec(goal))
    plan = read_template("plan.md").replace("{{ goal }}", goal)
    write_run_text(run, "plan.md", plan)
    write_text_safely(root / ".aiflow" / "plan.md", plan, force=True)

    state = initial_state(run.run_id, goal)
    state["status"] = "planned"
    state["stages"]["context"] = "done"
    state["stages"]["spec"] = "done"
    state["stages"]["plan"] = "done"
    save_state(run, state)
    set_current_run(root, run.run_id)
    append_event(run, "run.created", "Created workflow run")
    append_event(run, "context.generated", "Generated run context")
    append_event(run, "spec.generated", "Generated task spec draft")
    append_event(run, "plan.generated", "Generated implementation plan draft")
    return run


def load_run(root: Path, run_id: str | None = None) -> WorkflowRun:
    current = run_id or current_run(root)
    if not current:
        raise ValueError("No workflow run selected. Run `aiflow workflow start <goal>` first.")
    run = WorkflowRun(root=root, run_id=current)
    if not run.path.exists():
        raise ValueError(f"Workflow run not found: {current}")
    return run


def current_run(root: Path) -> str:
    path = current_run_path(root)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def set_current_run(root: Path, run_id: str) -> None:
    path = current_run_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(run_id + "\n", encoding="utf-8", newline="\n")


def initial_state(run_id: str, goal: str) -> dict[str, Any]:
    stamp = now_stamp()
    return {
        "id": run_id,
        "goal": goal,
        "status": "created",
        "created_at": stamp,
        "updated_at": stamp,
        "stages": {stage: "pending" for stage in STAGES},
    }


def read_state(run: WorkflowRun) -> dict[str, Any]:
    return json.loads((run.path / "state.json").read_text(encoding="utf-8"))


def save_state(run: WorkflowRun, state: dict[str, Any]) -> None:
    state["updated_at"] = now_stamp()
    write_json(run.path / "state.json", state)


def mark_stage(run: WorkflowRun, stage: str, status: str, *, run_status: str | None = None) -> None:
    state = read_state(run)
    state.setdefault("stages", {})[stage] = status
    if run_status is not None:
        state["status"] = run_status
    save_state(run, state)


def append_event(run: WorkflowRun, event_type: str, message: str, **extra: Any) -> None:
    payload = {"time": now_stamp(), "type": event_type, "message": message, **extra}
    path = run.path / "events.jsonl"
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_run_text(run: WorkflowRun, name: str, content: str) -> Path:
    path = run.path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def build_spec(goal: str) -> str:
    return f"""# Task Spec

## Goal

{goal}

## Non-goals

- Do not write user-global configuration.
- Do not automatically commit, push, or publish.

## Allowed Changes

- TBD

## Required Verification

- `aiflow workflow verify`

## Risks

- TBD

## Open Questions

- TBD
"""


def unique_run_id(base: Path, goal: str) -> str:
    prefix = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    slug = slugify(goal) or "workflow"
    candidate = f"{prefix}-{slug}"
    if not (base / candidate).exists():
        return candidate
    index = 2
    while (base / f"{candidate}-{index}").exists():
        index += 1
    return f"{candidate}-{index}"


def slugify(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    text = re.sub(r"-+", "-", text)
    return text[:48].strip("-")

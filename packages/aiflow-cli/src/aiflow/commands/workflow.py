from __future__ import annotations

import json
from argparse import Namespace

from ..core.paths import project_root
from ..core.workflow import (
    append_event,
    create_run,
    current_run,
    load_run,
    mark_stage,
    read_state,
    set_current_run,
    write_run_text,
)
from .context import run_context
from .plan import run_plan
from .review import run_review, run_review_report
from .verify import run_verification, run_verify


WORKFLOW_COMMANDS = {"start", "status", "resume", "verify", "review", "finish"}


def run_workflow(args: Namespace) -> int:
    tokens = list(args.goal)
    if tokens and tokens[0] in WORKFLOW_COMMANDS:
        command = tokens[0]
        rest = tokens[1:]
        if command == "start":
            return workflow_start(rest)
        if command == "status":
            return workflow_status(rest)
        if command == "resume":
            return workflow_resume(rest)
        if command == "verify":
            return workflow_verify(rest, args)
        if command == "review":
            return workflow_review(rest)
        if command == "finish":
            return workflow_finish(rest)

    return run_legacy_workflow(args)


def workflow_start(tokens: list[str]) -> int:
    goal = " ".join(tokens).strip()
    if not goal:
        print("workflow start requires a goal")
        return 2
    root = project_root()
    run = create_run(root, goal)
    print(f"created: {run.path.relative_to(root)}")
    print("status: planned")
    print("next: implement according to spec.md and plan.md")
    return 0


def workflow_status(tokens: list[str]) -> int:
    root = project_root()
    try:
        run = load_run(root, tokens[0] if tokens else None)
    except ValueError as exc:
        print(str(exc))
        return 2
    state = read_state(run)
    print(f"Run: {run.run_id}")
    print(f"Goal: {state.get('goal', '')}")
    print(f"Status: {state.get('status', '')}")
    print("")
    print("Stages:")
    for name, value in state.get("stages", {}).items():
        print(f"- {name}: {value}")
    return 0


def workflow_resume(tokens: list[str]) -> int:
    root = project_root()
    try:
        run = load_run(root, tokens[0] if tokens else None)
    except ValueError as exc:
        print(str(exc))
        return 2
    set_current_run(root, run.run_id)
    state = read_state(run)
    print(f"Run: {run.run_id}")
    print(f"Goal: {state.get('goal', '')}")
    print(f"Spec: {run.path / 'spec.md'}")
    print(f"Plan: {run.path / 'plan.md'}")
    print(f"Status: {state.get('status', '')}")
    return 0


def workflow_verify(tokens: list[str], args: Namespace) -> int:
    root = project_root()
    try:
        run = load_run(root, tokens[0] if tokens else None)
    except ValueError as exc:
        print(str(exc))
        return 2
    result = run_verification(
        root,
        run.path,
        dry_run=False,
        continue_on_error=bool(args.continue_on_error or args.check),
        auto=not args.no_auto_verify,
    )
    ok = bool(result.get("ok"))
    mark_stage(run, "verify", "done" if ok else "failed", run_status="verified" if ok else "blocked")
    append_event(run, "verify.completed", "Workflow verification completed", ok=ok)
    print(f"written: {run.path.relative_to(root) / 'verify.md'}")
    print(f"written: {run.path.relative_to(root) / 'verify.json'}")
    return int(result.get("exit_code", 0))


def workflow_review(tokens: list[str]) -> int:
    root = project_root()
    try:
        run = load_run(root, tokens[0] if tokens else None)
    except ValueError as exc:
        print(str(exc))
        return 2
    result = run_review_report(root, run.path)
    ok = bool(result.get("ok"))
    mark_stage(run, "review", "done" if ok else "failed", run_status="reviewed" if ok else "blocked")
    append_event(run, "review.completed", "Workflow review completed", ok=ok)
    print(f"written: {run.path.relative_to(root) / 'review.md'}")
    print(f"written: {run.path.relative_to(root) / 'review.json'}")
    return 0 if ok else 1


def workflow_finish(tokens: list[str]) -> int:
    root = project_root()
    try:
        run = load_run(root, tokens[0] if tokens else None)
    except ValueError as exc:
        print(str(exc))
        return 2

    verify = read_json(run.path / "verify.json")
    if not verify.get("ok"):
        print("Cannot finish: verification has not passed.")
        return 2
    review = read_json(run.path / "review.json")
    if not review.get("ok"):
        print("Cannot finish: review has not passed.")
        return 2
    blocking = [finding for finding in review.get("findings", []) if finding.get("blocking") and finding.get("status") != "closed"]
    if blocking:
        print("Cannot finish: blocking review findings are still open.")
        return 2

    state = read_state(run)
    summary = f"""# Workflow Summary

## Goal

{state.get('goal', '')}

## Status

Delivered.

## Verification

Verification: passed

## Review

Review: passed
"""
    write_run_text(run, "summary.md", summary)
    mark_stage(run, "finish", "done", run_status="delivered")
    append_event(run, "run.delivered", "Workflow run delivered")
    print(f"delivered: {run.path.relative_to(root)}")
    print(f"summary: {run.path.relative_to(root) / 'summary.md'}")
    return 0


def run_legacy_workflow(args: Namespace) -> int:
    verify_requested = bool(args.verify or args.check)
    review_requested = bool(args.review or args.check)
    goal = " ".join(args.goal).strip()

    if args.dry_run:
        print("Workflow dry-run:")
        print(f"- context: aiflow context{'' if args.no_compact else ' --compact'}")
        if goal and not args.skip_plan:
            print(f"- plan: aiflow plan {goal}")
        elif args.skip_plan:
            print("- plan: skipped by --skip-plan")
        else:
            print("- plan: skipped because no goal was provided")
        if verify_requested:
            flags = ["--auto"] if not args.no_auto_verify else []
            if args.continue_on_error or args.check:
                flags.append("--continue-on-error")
            print(f"- verify: aiflow verify {' '.join(flags)}".rstrip())
        if review_requested:
            print("- review: aiflow review")
        return 0

    print("Running workflow step: context")
    run_context(Namespace(output=None, compact=not args.no_compact))

    if goal and not args.skip_plan:
        print("Running workflow step: plan")
        run_plan(Namespace(goal=args.goal, force=args.force_plan))
    elif args.skip_plan:
        print("Skipping workflow step: plan (--skip-plan)")
    else:
        print("Skipping workflow step: plan (no goal)")

    exit_code = 0
    continue_after_verify = bool(args.continue_on_error or args.check)
    if verify_requested:
        print("Running workflow step: verify")
        exit_code = run_verify(
            Namespace(
                dry_run=False,
                continue_on_error=continue_after_verify,
                auto=not args.no_auto_verify,
            )
        )
        if exit_code != 0 and not continue_after_verify:
            return exit_code

    if review_requested:
        print("Running workflow step: review")
        review_code = run_review(Namespace(output=None))
        if exit_code == 0:
            exit_code = review_code

    return exit_code


def read_json(path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

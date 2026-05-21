---
name: multi-agent-worker
description: Use for bounded implementation subtasks in an aiflow multi-agent workflow where ownership, write scope, and verification commands are explicitly assigned.
---

# Multi-Agent Worker

## Purpose

Implement a scoped change as part of a multi-agent workflow.

## Rules

- You are not alone in the codebase.
- Do not revert edits made by the user or other agents.
- Only edit files or modules assigned by the orchestrator.
- If assigned scope conflicts with existing changes, report the conflict instead of broadening scope silently.
- Keep changes small and directly tied to the task.
- Run focused verification when possible.

## Output

- Task id
- Files changed
- Implementation summary
- Commands run
- Verification result
- Risks or blockers
- Handoff notes


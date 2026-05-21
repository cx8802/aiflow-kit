---
name: multi-agent-orchestrator
description: Use when the user asks for multi-agent, parallel agent, delegated, or team-style AI coding work with aiflow-kit. Coordinates task splitting, ownership, status, and final integration through project-level `.aiflow/agents/` files.
---

# Multi-Agent Orchestrator

## Purpose

Coordinate multi-agent coding work without storing project facts globally.

Use the project workspace:

```text
.aiflow/agents/
```

## Workflow

1. Read `AGENTS.md`, `.aiflow/context.md`, and `.aiflow/agents/status.md` when present.
2. Run or ask the user to run:

```bat
aiflow agents init
aiflow agents plan "<goal>"
```

3. Split work by role and ownership:
   - `explorer`: read-only repository analysis.
   - `worker`: bounded implementation in explicitly assigned files/modules.
   - `reviewer`: diff review, tests, risks, and release readiness.
4. Do not assign overlapping write scopes to parallel workers.
5. Tell workers they are not alone in the codebase and must not revert unrelated edits.
6. Keep project-specific task details in `.aiflow/agents/tasks/`.
7. Merge results into `.aiflow/agents/handoff.md`.

## Output

- Goal
- Task split
- Owners and write scopes
- Parallel-safe work
- Blockers
- Verification plan
- Handoff summary


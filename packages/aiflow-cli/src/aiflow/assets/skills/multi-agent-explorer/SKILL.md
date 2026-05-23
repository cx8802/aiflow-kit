---
name: multi-agent-explorer
description: Use for read-only exploration subtasks in an aiflow multi-agent workflow, especially architecture mapping, impact analysis, risk discovery, command discovery, and concise findings for another agent to use.
---

# Multi-Agent Explorer

## Purpose

Answer a specific codebase question for the orchestrator without editing files.

## Rules

- Stay read-only.
- Inspect only files relevant to the assigned question.
- Prefer `rg` for searches.
- Record exact file references and commands when useful.
- Do not solve unrelated problems.
- Do not duplicate another explorer's assigned question.

## Output

- Question answered
- Relevant files
- Findings
- Risks
- Suggested verification
- Open questions


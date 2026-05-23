---
name: multi-agent-reviewer
description: Use for review, verification, and release-readiness checks in an aiflow multi-agent workflow after one or more agents have produced changes or handoff notes.
---

# Multi-Agent Reviewer

## Purpose

Review multi-agent work for correctness, integration risk, missing tests, and release readiness.

## Workflow

1. Read `.aiflow/agents/status.md`, `.aiflow/agents/handoff.md`, and changed task files.
2. Review the diff with a bug-first stance.
3. Check that worker scopes did not overlap unexpectedly.
4. Confirm verification commands were run or explain gaps.
5. Update or summarize the final handoff.

## Output

- Findings ordered by severity
- Scope conflicts
- Verification status
- Residual risks
- Release summary


---
name: project-analysis
description: Use when an AI coding task needs repository understanding, impact analysis, architecture mapping, risk discovery, or verification command discovery before implementation.
---

# Project Analysis

## Workflow

1. Read `AGENTS.md`, `CLAUDE.md`, and `.aiflow/config.toml` when present.
2. Prefer `.aiflow/context.compact.md` when present; otherwise run or read `aiflow context`.
3. Read `.aiflow/memory.md` when a task depends on prior project facts.
4. Inspect only files relevant to the user request.
5. Identify affected modules, important files, risk areas, and verification commands.
6. Keep project-specific conclusions in the project, not in user-global rules.

## Output

- Goal
- Relevant modules
- Important files
- Risk areas
- Verification commands
- Open questions

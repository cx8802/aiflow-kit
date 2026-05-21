---
name: project-analysis
description: Use when an AI coding task needs repository understanding, impact analysis, architecture mapping, risk discovery, or verification command discovery before implementation.
---

# Project Analysis

## Workflow

1. Read `AGENTS.md`, `CLAUDE.md`, and `.aiflow/config.toml` when present.
2. Run or read `aiflow context` if `.aiflow/context.md` is missing or stale.
3. Inspect only files relevant to the user request.
4. Identify affected modules, important files, risk areas, and verification commands.
5. Keep project-specific conclusions in the project, not in user-global rules.

## Output

- Goal
- Relevant modules
- Important files
- Risk areas
- Verification commands
- Open questions

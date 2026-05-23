# AI Agent Instructions

## Project Workflow

- Before non-trivial changes, run or read `.aiflow/context.compact.md` when present; otherwise run or read `.aiflow/context.md`.
- For implementation work, create or update `.aiflow/plan.md`.
- Before final response or commit, run configured verification or explain why it was not run.
- Keep project-specific facts inside this repository. Do not write user-global configuration unless explicitly requested.
- Store reusable project facts with `aiflow memory add`; do not store secrets in memory.

## Commands

- Context: `aiflow context`
- Compact context: `aiflow compact`
- Memory: `aiflow memory list`
- Review: `aiflow review`
- Verify: `aiflow verify`

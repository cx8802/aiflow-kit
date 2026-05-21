# Plan: multi-agent workflow support

## Goal

Add a lightweight multi-agent coordination layer for `aiflow-kit` so Codex and Claude Code can split larger coding work into bounded roles, project-level task files, status, and handoff notes.

## Non-goals

- Do not build a background scheduler, queue service, or cloud platform.
- Do not store project tasks in global Codex or Claude configuration.
- Do not require any provider-specific subagent implementation.

## Impact scope

- `src/aiflow/core/agents.py`
- `src/aiflow/commands/agents.py`
- `src/aiflow/cli.py`
- `src/aiflow/assets/skills/*`
- `tests/test_cli_smoke.py`
- `docs/17-多Agent协作流程.md`
- `docs/README.md`

## Steps

1. Define `.aiflow/agents/` files: roles, tasks, status, and handoff.
2. Add `aiflow agents init/plan/status/handoff` commands.
3. Add global reusable Skills for orchestrator, explorer, worker, and reviewer behavior.
4. Document global vs project-level boundaries and Codex/Claude usage.
5. Add focused smoke tests for generated files and command output.

## Verification

- `python -m compileall -q src tests`
- `python -m unittest discover -s tests`
- `aiflow verify --continue-on-error`

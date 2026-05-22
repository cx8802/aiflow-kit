# Plan

Reduce default aiflow Claude Agent SDK context payload while keeping project-local MiniMax environment settings isolated from user-level Claude Code settings.

## Goal

- Keep `aiflow claude-agent` isolated from `~/.claude/settings.json` provider/model env.
- Continue using `.aiflow/claude-agent.local.toml` for project-local secrets and model environment.
- Prefer compact context over full context to reduce token usage.
- Keep Claude Agent default context small enough that aiflow remains token-saving.
- Keep explicit compact commands able to read richer source context and produce `.aiflow/context.compact.md`.
- Preserve read-only default permissions and existing run artifacts.

## Non-goals

- Do not modify user-global Claude Code settings.
- Do not commit secrets.
- Do not change default tool permissions.

## Impact Scope

- `node/claude-agent-runner/runner.mjs`
- `src/aiflow/core/claude_agent.py`
- `src/aiflow/core/config.py`
- `src/aiflow/assets/templates/config.toml`
- `tests/test_cli_smoke.py`

## Steps

1. Done: Reproduce MiniMax run being overridden by user-level deepseek settings.
2. Done: Pass isolated SDK settings/env from the runner.
3. Done: Add a runner smoke test for `settingSources` and env propagation.
4. Done: Re-test real MiniMax run and project verification.
5. Done: Stop sending full `.aiflow/context.md` when compact context exists.
6. Done: Add strict default context caps and disable memory injection by default.
7. Done: Route `claude-agent compact` through compression source files instead of normal small context.
8. Done: Add explicit context levels, dry-run context budget, usage summaries, and strict edit scope.
9. Done: Add configurable diff truncation for review-diff prompts.

## Verification

- `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_claude_agent_runner_passes_budget_to_sdk`
- `scripts\aiflow-dev.bat claude-agent run "Return exactly: minimax model works." --model small`
- `scripts\aiflow-dev.bat verify --auto --continue-on-error`

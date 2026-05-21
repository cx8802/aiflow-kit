# Implementation Plan

## Goal

Configure the project-local Claude Agent runner for MiniMax without writing the provided token into tracked files, then verify a live Agent SDK run.

## Non-goals

- Do not add user-global environment variables for the MiniMax token.
- Do not widen Claude Agent tool permissions beyond the existing read-only defaults.
- Do not make MiniMax provider settings part of the package defaults.

## Impact Scope

- `.aiflow/config.toml`
- `.aiflow/claude-agent.local.toml` for ignored local env values
- `src/aiflow/core/claude_agent.py`
- `src/aiflow/commands/claude_agent.py`
- `node/claude-agent-runner/runner.mjs`
- `tests/test_cli_smoke.py`

## Steps

1. Read project-local env from `.aiflow/claude-agent.local.toml` for Claude Agent subprocesses.
2. Map MiniMax auth token and base URL variables into the Anthropic-compatible runtime env.
3. Pass the installed `claude` executable path to the Agent SDK on Windows.
4. Configure this repository to use the `MiniMax-M2.7` model alias and install the project-local SDK.
5. Run focused tests, repository verification, and a one-turn live MiniMax probe.

## Verification

- `python -m unittest discover -s tests`
- `.\.venv\Scripts\aiflow.exe verify --auto`
- `.\.venv\Scripts\python.exe -m compileall src`
- `.\.venv\Scripts\aiflow.exe claude-agent doctor`
- Live run expecting `MINIMAX_AGENT_OK`

## Risks

- The live probe consumes provider tokens and budget.
- The provided token stays in an ignored local TOML file and must remain uncommitted.
- Agent SDK and installed Claude Code CLI versions can diverge on future upgrades.

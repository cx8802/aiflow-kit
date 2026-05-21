# Implementation Plan

## Goal

Keep Claude Agent SDK dependencies owned by `aiflow-kit` instead of installing a duplicate Node SDK tree into every target repository.

## Non-goals

- Do not move run artifacts, local secrets, or target-project context out of the target repository.
- Do not change frontend Playwright tooling ownership.
- Do not require target repositories to install Node dependencies for Claude Agent use.

## Impact Scope

- `src/aiflow/core/claude_agent.py`
- `src/aiflow/commands/claude_agent.py`
- `tests/test_cli_smoke.py`
- `docs/22-Claude-Agent-SDK设计方案.md`

## Steps

1. Add tests proving Claude Agent SDK installs resolve to the `aiflow-kit` tool directory.
2. Resolve relative Claude Agent SDK package paths against `aiflow-kit`, keeping absolute overrides intact.
3. Update command text and design docs so dependency ownership is explicit.
4. Run focused tests and repository verification.

## Verification

- `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_claude_agent_install_dry_run_uses_aiflow_kit_sdk_package`
- `python -m unittest discover -s tests`
- `.\.venv\Scripts\aiflow.exe verify --auto`
- `.\.venv\Scripts\python.exe -m compileall src`

## Risks

- Source checkout and installed-package layouts must still resolve the bundled runner and SDK directory consistently.
- Absolute `package_dir` overrides should remain explicit escape hatches.
- Target repositories still keep `.aiflow/claude-agent/` run outputs and ignored local secret files.

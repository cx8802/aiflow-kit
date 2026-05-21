# Implementation Plan

## Goal

Keep Claude Agent SDK runtime ownership in `aiflow-kit`, while target projects own only Claude Agent enablement, model/provider policy, permissions, budget, secrets, and run artifacts.

## Non-goals

- Do not move run artifacts, local secrets, or target-project context out of the target repository.
- Do not change frontend Playwright tooling ownership.
- Do not expose `package_dir` or runner path knobs in newly generated project config.

## Impact Scope

- `src/aiflow/assets/templates/config.toml`
- `src/aiflow/core/claude_agent.py`
- `src/aiflow/core/config.py`
- `tests/test_cli_smoke.py`
- `docs/22-Claude-Agent-SDK设计方案.md`

## Steps

1. Add tests proving generated project config excludes kit-owned Claude Agent runtime paths.
2. Remove kit-owned `package_dir` and runner path fields from project defaults, templates, and validation.
3. Keep core runtime resolution inside `aiflow-kit`.
4. Update design docs so project-level policy and kit-level runtime ownership are explicit.
5. Run focused tests and repository verification.

## Verification

- `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_init_keeps_claude_agent_runtime_paths_out_of_project_config`
- `python -m unittest discover -s tests`
- `.\.venv\Scripts\aiflow.exe verify --auto`
- `.\.venv\Scripts\python.exe -m compileall src`

## Risks

- Source checkout and installed-package layouts must still resolve the bundled runner and SDK directory consistently.
- Existing project configs that still contain `package_dir` or `runner` should not break reads.
- Target repositories still keep `.aiflow/claude-agent/` run outputs and ignored local secret files.

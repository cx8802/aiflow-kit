# Plan: Claude Agent SDK MVP

## Goal

Implement a Node-based Claude Agent SDK MVP for aiflow-kit, with project-local install, custom API/model configuration, safe default permissions, and run outputs under `.aiflow/claude-agent/`.

## Non-goals

- Do not hard-code API keys, base URLs, or model names.
- Do not require global npm installs.
- Do not allow write/edit permissions by default.
- Do not require a real Anthropic API key for dry-run, doctor, or unit tests.
- Do not make SDK execution part of default verify.

## Impact scope

- `src/aiflow/commands/claude_agent.py`
- `src/aiflow/core/claude_agent.py`
- `node/claude-agent-runner/runner.mjs`
- `node/claude-agent-runner/package.json`
- `src/aiflow/cli.py`
- `src/aiflow/core/config.py`
- `src/aiflow/assets/templates/config.toml`
- `tests/test_cli_smoke.py`
- `docs/22-Claude-Agent-SDK设计方案.md`
- `docs/README.md`

## Steps

1. Add `[claude_agent]` config defaults and validation.
2. Add project-local SDK install and doctor checks.
3. Add Node runner that imports `@anthropic-ai/claude-agent-sdk`, executes read-only queries, and writes run artifacts.
4. Add CLI commands: `install`, `doctor`, `run`, `explore`, `review-diff`, `compact`, `usage`.
5. Add tests for dry-run, config validation, input generation, and usage listing.
6. Update docs with implemented command behavior.

## Verification

- `python -m compileall -q src tests`
- `python -m unittest discover -s tests`
- `aiflow claude-agent doctor`
- `aiflow claude-agent run "..." --dry-run`
- Run `git diff --check`.

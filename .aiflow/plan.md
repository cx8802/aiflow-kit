# Plan: dynamic install path and environment config

## Goal

Make `aiflow-kit` portable across machines by detecting the real source path and local tool environment during install, then rendering Codex/Claude Skills with the detected path instead of hard-coded examples.

## Non-goals

- Do not write permanent user environment variables.
- Do not commit machine-local environment files.
- Do not require PowerShell scripts.

## Impact scope

- `src/aiflow/core/environment.py`
- `src/aiflow/commands/env.py`
- `src/aiflow/commands/install_skills.py`
- `src/aiflow/commands/doctor.py`
- `src/aiflow/cli.py`
- `scripts/quick-install.bat`
- `scripts/aiflow-update.bat`
- `src/aiflow/assets/skills/aiflow-kit-*`
- `tests/test_cli_smoke.py`
- `docs/18-安装路径与环境探测.md`
- `docs/README.md`

## Steps

1. Add environment detection that reports project root, aiflow-kit root, scripts, plugin dirs, proxy, and tool versions.
2. Write `.aiflow/env.local.toml` as the editable machine-local config.
3. Render bundled Skills with the detected aiflow-kit root during install.
4. Make quick install and update scripts run environment detection first.
5. Update docs and tests.

## Verification

- `python -m compileall -q src tests`
- `python -m unittest discover -s tests`
- `aiflow verify --continue-on-error`

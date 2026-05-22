# Plan

Add WSL and SSH operation commands to aiflow-kit.

## Goal

- Provide `aiflow wsl` commands for WSL availability checks, distro listing, command execution, and path conversion.
- Provide `aiflow ssh` commands for project-level SSH profiles and remote command execution.
- Keep secrets out of tracked config by requiring `.aiflow/*.local.toml` or environment variable names.

## Non-goals

- Do not implement an interactive terminal UI.
- Do not store SSH passwords or private key contents in tracked files.
- Do not require WSL or SSH to be installed for unit tests.

## Impact Scope

- `src/aiflow/cli.py`
- `src/aiflow/commands/wsl.py`
- `src/aiflow/commands/ssh.py`
- `src/aiflow/core/remote.py`
- `tests/test_cli_smoke.py`
- `docs/README.md`

## Steps

1. Done: Read project context and existing command/profile patterns.
2. Done: Implement WSL command helpers and CLI parser.
3. Done: Implement SSH profile storage, redaction, dry-run, and execution.
4. Done: Register commands and add smoke tests.
5. Done: Update docs and run verification.

## Verification

- `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_wsl_*`
- `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_ssh_*`
- `python -m unittest discover -s tests`
- `git diff --check`

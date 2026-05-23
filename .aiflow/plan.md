# Plan

## Non-Commercial v0.1.2 Release Plan

### Goal

- Change the project license from Apache-2.0 to a non-commercial source-available license.
- Bump the Python CLI and plugin manifest versions to `0.1.2`.
- Publish `v0.1.2` to both Gitee and GitHub after verification.

### Non-goals

- Do not add a commercial license grant.
- Do not write tokens or credentials into repository files.
- Do not create user-global configuration.

### Impact Scope

- `LICENSE`
- `NOTICE`
- `README.md`
- `CHANGELOG.md`
- `packages/aiflow-cli/pyproject.toml`
- `packages/aiflow-cli/src/aiflow/__init__.py`
- `packages/aiflow-cli/src/aiflow/commands/install_skills.py`
- `packages/aiflow-cli/tests/test_cli_smoke.py`
- `.aiflow/plan.md`
- `.aiflow/memory.md`

### Steps

1. Done: Add a failing metadata test for the non-commercial license and `0.1.2` version.
2. Done: Replace Apache metadata with the AIFLOW-KIT non-commercial license metadata.
3. Done: Run focused tests, full smoke tests, configured verification, and diff checks.
4. Pending: Commit, tag `v0.1.2`, push to Gitee and GitHub, and create platform releases if credentials are available.

### Verification

- Failed as expected: `python -m unittest packages.aiflow-cli.tests.test_cli_smoke.CliSmokeTests.test_release_metadata_uses_non_commercial_license`
- Passed: `python -m unittest packages.aiflow-cli.tests.test_cli_smoke.CliSmokeTests.test_release_metadata_uses_non_commercial_license`
- Passed: `python -m unittest discover -s packages\aiflow-cli\tests -p test_cli_smoke.py` (71 tests, 1 skipped because `sh` is unavailable on this Windows host)
- Passed: `cmd /c scripts\win\aiflow-dev.bat verify --auto --continue-on-error`
- Passed: `git diff --check`
- Passed: `cmd /c scripts\win\aiflow-dev.bat --version`
- Passed: `python -m pip wheel packages\aiflow-cli -w .cache\wheels`
- Passed: `cmd /c scripts\win\aiflow-dev.bat review`

## CMD Project Install Launcher Plan

### Goal

- Add a CMD-friendly way to use aiflow from any project directory.
- Provide a one-command project-level installer for the current directory.
- Keep default behavior project-local and avoid user-level global writes.

### Non-goals

- Do not modify permanent user PATH automatically.
- Do not install skills into Codex/Claude user directories by default.
- Do not overwrite existing project `AGENTS.md` or `CLAUDE.md` without explicit force behavior.

### Impact Scope

- `scripts/aiflow-env.bat`
- `scripts/aiflow-install.bat`
- `packages/aiflow-cli/tests/test_cli_smoke.py`
- `packages/aiflow-cli/src/aiflow/assets/skills/aiflow-kit-installer/SKILL.md`
- `README.md`
- Install-related docs
- `.aiflow/plan.md`

### Steps

1. Done: Add regression tests for the launcher scripts.
2. Done: Implement current-session environment and install launcher scripts.
3. Done: Update skill and docs.
4. Done: Run focused and configured verification.

### Verification

- Passed: `python -m unittest discover -s packages\aiflow-cli\tests -p test_cli_smoke.py -k cmd_launchers -k aiflow_install_bat`
- Passed: `cmd /c scripts\aiflow-env.bat`
- Passed: `python -m unittest discover -s packages\aiflow-cli\tests -p test_cli_smoke.py`
- Passed: `cmd /c scripts\aiflow-dev.bat verify --auto --continue-on-error`
- Passed: `git diff --check`

## Project-Local Aiflow CLI Install Plan

### Goal

- Make `packages/aiflow-cli` install into the repository `.venv` by default.
- Keep quick install and update flows project-local unless the user explicitly opts into user-level global skills.
- Preserve local plugin package generation under `.aiflow/dist/`.

### Non-goals

- Do not remove existing user-level skills automatically.
- Do not write user-global configuration by default.
- Do not change the `install-skills` explicit global target guard.

### Impact Scope

- `scripts/aiflow-dev.bat`
- `scripts/quick-install.bat`
- `scripts/aiflow-update.bat`
- `packages/aiflow-cli/tests/test_cli_smoke.py`
- `README.md`
- Install-related docs
- `.aiflow/plan.md`

### Steps

1. Done: Add regression tests for project-local install defaults.
2. Done: Update scripts to create/use `.venv` and avoid user skills by default.
3. Done: Update docs to describe project-level install first.
4. Done: Run focused and configured verification.

### Verification

- Passed: `python -m unittest discover -s packages\aiflow-cli\tests -p test_cli_smoke.py -k quick_install -k update_help -k codex_user_install_requires_explicit_global_flags`
- Passed: `.venv\Scripts\python.exe -m pip install -e packages\aiflow-cli`
- Passed: `python -m unittest discover -s packages\aiflow-cli\tests -p test_cli_smoke.py`
- Passed: `cmd /c scripts\aiflow-dev.bat verify --auto --continue-on-error`
- Passed: `git diff --check`

## Python CLI Workspace Layout Plan

### Goal

- Move the Python CLI package out of the repository root into `packages/aiflow-cli/`.
- Keep the repository root as the multi-project kit workspace containing apps, extensions, node tooling, docs, scripts, and packages.
- Preserve development commands through `scripts/aiflow-dev.bat`.

### Non-goals

- Do not change CLI behavior.
- Do not move GUI, browser extension, node runner, docs, or runtime artifact directories.
- Do not write user-global configuration.

### Impact Scope

- `packages/aiflow-cli/pyproject.toml`
- `packages/aiflow-cli/src/`
- `packages/aiflow-cli/tests/`
- `scripts/aiflow-dev.bat`
- `scripts/quick-uninstall.bat`
- `README.md`
- Key docs that mention editable install, test paths, or `src/aiflow`
- `.aiflow/config.toml`
- `.aiflow/plan.md`

### Steps

1. Done: Add a layout regression test for the new Python CLI package root.
2. Done: Move `pyproject.toml`, `src/`, and `tests/` under `packages/aiflow-cli/`.
3. Done: Update path discovery, dev script `PYTHONPATH`, uninstall skill source path, tests, and docs.
4. Done: Run focused and configured verification.

### Verification

- Passed: layout regression test, included in Python CLI smoke suite
- Passed: `python -m unittest discover -s packages\aiflow-cli\tests -p test_cli_smoke.py`
- Passed: `cmd /c scripts\aiflow-dev.bat --version`
- Passed: `cmd /c scripts\aiflow-dev.bat verify --auto --continue-on-error`
- Passed: `python -m pip wheel packages\aiflow-cli -w .cache\wheels`
- Passed: `git diff --check`

Tighten the boundary between updating aiflow-kit itself and installing aiflow-kit into a target project.

## Goal

- Generic requests like "update this" must not trigger aiflow installation in another project.
- Updating aiflow/aiflow-kit should refresh global skills and plugin packages by default.
- Project-level aiflow files should be created or refreshed only when explicitly requested.

## Non-goals

- Do not change unrelated browser, Claude Agent, or database work in the tree.
- Do not write user-global configuration outside the existing update flow.
- Do not change project templates beyond updater guidance.

## Impact Scope

- `scripts/aiflow-update.bat`
- `src/aiflow/assets/skills/aiflow-kit-updater/SKILL.md`
- `src/aiflow/assets/skills/aiflow-kit-guide/SKILL.md`
- `.agents/skills/aiflow-kit-updater/SKILL.md`
- `.agents/skills/aiflow-kit-guide/SKILL.md`
- `.aiflow/plan.md`

## Steps

1. Done: Read compact project context and current updater/installer skill instructions.
2. Done: Make the update script global-only by default, with explicit project flags.
3. Done: Update skill guidance so only explicit aiflow/aiflow-kit requests invoke updater behavior.
4. Done: Run focused verification.

## Verification

- Passed: `cmd /c "scripts\aiflow-update.bat --help & exit /b 0"`
- Passed: `git diff --check`
- Passed: `scripts\aiflow-dev.bat verify --auto --continue-on-error`

---

## CodeGraph And Graphify Layer Implementation Plan

### Goal

- Split code structure facts and project knowledge facts into separate generated layers.
- Add `CodeGraph` for deterministic code structure scans.
- Add `Graphify` for project knowledge built from docs and project memory.

### Non-goals

- Do not implement a full graph database.
- Do not call external LLMs or network services.
- Do not replace `aiflow context` or `aiflow memory`.
- Do not auto-run CodeGraph or Graphify from workflow yet.

### Impact Scope

- `src/aiflow/core/codegraph.py`
- `src/aiflow/core/graphify.py`
- `src/aiflow/commands/codegraph.py`
- `src/aiflow/commands/graphify.py`
- `src/aiflow/cli.py`
- `tests/test_cli_smoke.py`
- `docs/26-全链条自动化开发差距分析与优化路线.md`
- `.gitignore`
- `.aiflow/plan.md`

### Steps

1. Done: Add failing tests for `aiflow codegraph scan` and `aiflow graphify build`.
2. Done: Implement deterministic Python CodeGraph scanning for modules, symbols, and entrypoints.
3. Done: Implement Graphify knowledge output from README, docs, and project memory.
4. Done: Register new CLI commands and ignore generated output directories.
5. Done: Run full repository verification.

### Verification

- Passed: `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_codegraph_scan_writes_code_structure_layer tests.test_cli_smoke.CliSmokeTests.test_graphify_build_writes_project_knowledge_layer`
- Passed: `git diff --check`
- Passed: `scripts\aiflow-dev.bat verify --auto --continue-on-error`

---

## Workflow Run Runtime Implementation Plan

### Goal

- Implement the minimal workflow run runtime described in `docs/26-全链条自动化开发差距分析与优化路线.md`.
- Add run containers, current run selection, state files, spec/context/plan artifacts, structured verification/review results, and finish gating.

### Non-goals

- Do not implement multi-agent run dispatch yet.
- Do not add GUI behavior.
- Do not automate commit, push, PR, or release.
- Do not change database, SSH, WSL, or Forge behavior beyond workflow gating hooks.

### Impact Scope

- `src/aiflow/core/workflow.py`
- `src/aiflow/commands/workflow.py`
- `src/aiflow/commands/verify.py`
- `src/aiflow/commands/review.py`
- `tests/test_cli_smoke.py`
- `.gitignore`
- `.aiflow/plan.md`

### Steps

1. Done: Add failing tests for `workflow start` run container creation and current-run verify/review/finish.
2. Done: Implement core workflow run state, current pointer, event log, spec/context/plan artifacts.
3. Done: Extend `workflow` command with `start/status/resume/verify/review/finish` while preserving legacy behavior.
4. Done: Add structured `verify.json` and `review.json` outputs for run-aware commands.
5. Done: Run full repository verification.

### Verification

- Passed: `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_workflow_start_creates_run_container tests.test_cli_smoke.CliSmokeTests.test_workflow_verify_review_and_finish_use_current_run`
- Passed: `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_workflow_generates_context_compact_and_plan tests.test_cli_smoke.CliSmokeTests.test_workflow_check_runs_verify_and_review tests.test_cli_smoke.CliSmokeTests.test_workflow_start_creates_run_container tests.test_cli_smoke.CliSmokeTests.test_workflow_verify_review_and_finish_use_current_run tests.test_cli_smoke.CliSmokeTests.test_review_handles_utf8_paths_on_windows tests.test_cli_smoke.CliSmokeTests.test_verify_auto_detects_unittest`
- Passed: `git diff --check`
- Passed: `scripts\aiflow-dev.bat verify --auto --continue-on-error`

---

## Current GUI Scaffold Plan

### Goal

- Add a Tauri 2 desktop GUI project for a future Claude Code and Codex desktop thread surface.
- Keep the frontend reusable as a React + Vite application inside the desktop shell.

### Non-goals

- Do not build the Python UI API or desktop process orchestration in this scaffold pass.
- Do not change existing browser extension, updater, or Claude Agent behavior.
- Do not write user-global configuration.

### Impact Scope

- `apps/aiflow-gui/`
- `README.md`
- `.aiflow/plan.md`

### Steps

1. Done: Confirm the official Tauri 2 generator command and local toolchain constraints.
2. Done: Generate a React + TypeScript Tauri 2 app under `apps/aiflow-gui`.
3. Done: Replace the generated starter UI with a Codex desktop-inspired project/thread/composer/review shell for Claude Code and Codex.
4. Done: Add repository-facing run notes for the new GUI project.
5. Done: Run focused frontend/build verification and record any Rust/toolchain gap.

### Verification

- Passed: `npm.cmd install` from `apps/aiflow-gui`
- Passed: `npm.cmd run build` from `apps/aiflow-gui`
- Passed: Playwright desktop/mobile GUI checks at `1440x900` and `390x844`
- Passed: `git diff --check`
- Passed: `scripts\aiflow-dev.bat verify --auto --continue-on-error`
- Passed: `scripts\aiflow-dev.bat review`
- Passed: `npm.cmd run tauri dev` and desktop window launch after Rust toolchain detection recovered
---

## Full-Chain Automation Document Optimization Plan

### Goal

- Tighten the full-chain automation analysis so it is more actionable for implementation.
- Make the document clearly distinguish current discrete-tool behavior from the target workflow run runtime.

### Non-goals

- Do not implement workflow runtime code in this pass.
- Do not change existing CLI behavior.
- Do not change installer, skills, or GUI files.

### Impact Scope

- `docs/26-全链条自动化开发差距分析与优化路线.md`
- `.aiflow/plan.md`

### Steps

1. Done: Review the first draft and identify missing implementation-level anchors.
2. Done: Rewrite the document around one-page conclusion, minimal viable loop, run files, commands, and phased rollout.
3. Done: Run repository verification.

### Verification

- Passed: `git diff --check`
- Passed: `scripts\aiflow-dev.bat verify --auto --continue-on-error`
---

## Windows Tauri Rust Install Path Plan

### Goal

- Update the Windows Tauri 2 development environment guide so Rust installs under `D:\Program Files\Rust`.

### Impact Scope

- `docs/other/Windows 创建 Tauri 2 开发环境.md`
- `.aiflow/plan.md`

### Steps

1. Done: Read compact project context and target documentation.
2. Done: Add `RUSTUP_HOME` and `CARGO_HOME` setup for `D:\Program Files\Rust`.
3. Done: Update the minimum workflow summary with the same Rust path setup.
4. Done: Run focused verification.

### Verification

- Passed: `git diff --check`
- Passed: `scripts\aiflow-dev.bat verify --auto --continue-on-error`

---

## Workflow Database Operations Plan

### Goal

- Make database operations available through the workflow entrypoint, not only through the standalone `aiflow db` command.
- Record database capabilities and configured profiles in each workflow run so agents can recover database context from the run directory.

### Non-goals

- Do not add new database drivers or change existing connection/query semantics.
- Do not store database secrets in tracked files or global configuration.
- Do not auto-run destructive database operations.

### Impact Scope

- `packages/aiflow-cli/src/aiflow/cli.py`
- `packages/aiflow-cli/src/aiflow/commands/db.py`
- `packages/aiflow-cli/src/aiflow/commands/workflow.py`
- `packages/aiflow-cli/src/aiflow/core/workflow.py`
- `packages/aiflow-cli/tests/test_cli_smoke.py`
- `README.md`
- `docs/15-数据库连接项目级配置.md`
- `docs/26-全链条自动化开发差距分析与优化路线.md`
- `.aiflow/plan.md`

### Steps

1. Done: Add failing tests for workflow run database capability recording and `workflow db` database operations.
2. Done: Refactor database command parser so workflow can reuse all db subcommands.
3. Done: Add `aiflow workflow db ...` as a workflow entrypoint for `add/list/show/test/tables/query`.
4. Done: Add database capability/profile summary to workflow run state and spec.
5. Done: Update docs for workflow-level database operations.

### Verification

- Passed: focused new workflow database tests.
- Passed: `python -m unittest discover -s packages\aiflow-cli\tests -p test_cli_smoke.py`
- Passed: `python -m aiflow workflow db --help`
- Passed: `cmd /c scripts\aiflow-dev.bat verify --auto --continue-on-error`
- Passed: `git diff --check`

---

## Cross-Platform Workflow Launcher Plan

### Goal

- Make the source workflow launchers usable on Windows CMD and macOS/Linux shells.
- Split platform-specific scripts into separate directories and remove redundant root command wrappers.
- Preserve project-local installation behavior and avoid permanent user environment writes by default.

### Non-goals

- Do not add PowerShell scripts.
- Do not write shell profiles, `setx`, or `launchctl setenv`.
- Do not change database command semantics.

### Impact Scope

- `scripts/win/`
- `scripts/mac/`
- `packages/aiflow-cli/tests/test_cli_smoke.py`
- `README.md`
- `docs/11-使用方式与安装策略.md`
- `docs/13-快速安装.md`
- `docs/16-在其他项目中安装aiflow-kit.md`
- `packages/aiflow-cli/src/aiflow/assets/skills/aiflow-kit-installer/SKILL.md`
- `.aiflow/plan.md`

### Steps

1. Done: Add failing tests for Unix/macOS launchers and project-local install behavior.
2. Done: Add shell launchers mirroring the Windows CMD workflow.
3. Done: Define current-shell `aiflow` and `aiflow-install` helpers from `aiflow-env.sh`.
4. Done: Update docs and installer skill with Windows and macOS/Linux usage.
5. Done: Move real Windows scripts to `scripts/win/` and real macOS/Linux scripts to `scripts/mac/`.
6. Done: Remove redundant root `scripts/` command wrappers.

### Verification

- Passed: focused Unix/macOS launcher tests, with execution skipped on this Windows host because `sh` is unavailable.
- Passed: `python -m unittest discover -s packages\aiflow-cli\tests -p test_cli_smoke.py` (69 tests, 1 skipped because `sh` is unavailable on this Windows host).
- Passed: `cmd /c scripts\aiflow-env.bat`
- Passed: `python -m aiflow workflow db --help`
- Passed: `cmd /c scripts\aiflow-dev.bat verify --auto --continue-on-error`
- Passed: `git diff --check`
- Passed: `git diff --cached --check`
- Passed: `git diff --cached --summary` confirmed Unix/macOS scripts are staged as mode `100755`.
- Passed: focused platform script split tests.
- Passed: `python -m unittest discover -s packages\aiflow-cli\tests -p test_cli_smoke.py` (70 tests, 1 skipped because `sh` is unavailable on this Windows host).
- Passed: `cmd /c scripts\aiflow-env.bat`
- Passed: `cmd /c scripts\win\aiflow-env.bat`
- Passed: `cmd /c scripts\win\aiflow-dev.bat --version`
- Passed: `cmd /c scripts\aiflow-dev.bat verify --auto --continue-on-error`
- Passed: `python -m aiflow workflow db --help`
- Passed: `git diff --check`
- Passed: `git diff --cached --check`
- Passed: focused no-root-wrapper script tests after deleting redundant root scripts.
- Passed after root wrapper deletion: `python -m unittest discover -s packages\aiflow-cli\tests -p test_cli_smoke.py` (70 tests, 1 skipped because `sh` is unavailable on this Windows host).
- Passed after root wrapper deletion: `cmd /c scripts\win\aiflow-dev.bat verify --auto --continue-on-error`.
- Passed after root wrapper deletion: `git diff --check` and `git diff --cached --check`.

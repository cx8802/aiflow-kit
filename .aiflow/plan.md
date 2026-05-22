# Plan

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

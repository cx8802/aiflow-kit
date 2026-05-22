# Plan

Remove machine-specific drive paths from Windows wrapper script documentation.

## Goal

- Make Windows wrapper examples portable across drives and checkout locations.
- Keep source-repo examples usable from the repository root.
- Use a placeholder for calling the source wrapper from another project.

## Non-goals

- Do not change wrapper script behavior.
- Do not write user-global PATH or config.
- Do not touch unrelated local changes.

## Impact Scope

- README and user-facing docs that mention the Windows wrapper path.
- `.aiflow/plan.md`

## Steps

1. Done: Read compact project context.
2. Done: Locate hard-coded local wrapper examples.
3. Done: Replace machine-specific paths with repo-relative commands or `%AIFLOW_KIT%`.
4. Done: Run lightweight verification.

## Verification

- Passed: source-path search across README, docs, `.agents`, `src`, `AGENTS.md`, and `CLAUDE.md` returned no matches for the old local checkout path.
- Passed: `git diff --check`
- Passed: `scripts\aiflow-dev.bat verify --auto --continue-on-error`

# Plan

Release aiflow-kit v0.1.1 with the bundled Gitee operation skill.

## Goal

- Add a reusable Skill for Gitee Git and OpenAPI operations.
- Cover releases, issues, pull requests, repository lookup, and token handling.
- Keep secrets out of tracked files and project memory.
- Bump package, CLI, and plugin manifest versions to `0.1.1`.
- Verify and publish `master` plus tag `v0.1.1` to Gitee.

## Non-goals

- Do not implement a new `aiflow gitee` CLI command in this step.
- Do not call live Gitee mutation APIs during validation.
- Do not modify user-global skill directories unless explicitly requested.
- Do not include unrelated existing docs/database local changes in the release commit.

## Impact Scope

- `src/aiflow/assets/skills/gitee-api/SKILL.md`
- `src/aiflow/__init__.py`
- `src/aiflow/commands/install_skills.py`
- `pyproject.toml`
- `tests/test_cli_smoke.py`
- `.aiflow/plan.md`

## Steps

1. Done: Read compact context, project rules, skill creation guidance, existing bundled skills, and install tests.
2. Done: Add the `gitee-api` bundled Skill.
3. Done: Add/update smoke coverage for bundled skill installation.
4. Done: Bump release versions to `0.1.1`.
5. In progress: Run verification, build sanity check, commit, tag, and push to Gitee.

## Verification

- Passed: `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_install_skills_defaults_to_project_codex_skills`
- Passed: `git diff --check`
- Passed: `scripts\aiflow-dev.bat verify --auto --continue-on-error`
- Passed: `scripts\aiflow-dev.bat review`
- Passed: release verification after version bump with `scripts\aiflow-dev.bat verify --auto --continue-on-error`.
- Passed: `python -m pip wheel . -w dist`.

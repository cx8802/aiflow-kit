# Plan

Organize Gitee and GitHub API references into bundled Skills.

## Goal

- Add concise API reference files under the Gitee and GitHub Skills.
- Keep `SKILL.md` as a small workflow entry point and move endpoint tables into `references/`.
- Include references in Python package data so installed Skills keep their API docs.
- Preserve token safety rules and prefer `aiflow forge` for supported release automation.

## Non-goals

- Do not call live mutation APIs during validation.
- Do not store or reuse exposed Gitee/GitHub tokens.
- Do not include unrelated existing docs/database local changes in this implementation.

## Impact Scope

- `src/aiflow/assets/skills/gitee-api/SKILL.md`
- `src/aiflow/assets/skills/gitee-api/references/api-reference.md`
- `src/aiflow/assets/skills/github-api/SKILL.md`
- `src/aiflow/assets/skills/github-api/references/api-reference.md`
- `pyproject.toml`
- `tests/test_cli_smoke.py`
- `.aiflow/plan.md`

## Steps

1. Done: Read skill creation guidance, current Gitee/GitHub Skills, package data config, and working tree state.
2. Done: Check Gitee SDK docs for Release, Issue, and Pull Request endpoint shapes.
3. Done: Add progressive-disclosure API references to both Skills.
4. Done: Ensure reference files are packaged and copied by `install-skills`.
5. Done: Run verification and review.

## Verification

- Passed: `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_install_skills_defaults_to_project_codex_skills`
- Passed: `git diff --check`
- Passed: `python -m pip wheel . -w dist`
- Passed: wheel contains `aiflow/assets/skills/gitee-api/references/api-reference.md` and `aiflow/assets/skills/github-api/references/api-reference.md`
- Passed: `scripts\aiflow-dev.bat verify --auto --continue-on-error`
- Passed: `scripts\aiflow-dev.bat review`

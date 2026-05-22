# Plan

Write a project README and prepare release-facing documentation.

## Goal

- Add a root project README suitable for repository and package landing pages.
- Keep the existing docs index available for detailed design documentation.
- Point package metadata at the project README for release packaging.
- Run repository verification before delivery.

## Non-goals

- Do not publish to PyPI, push git tags, or create a remote release.
- Do not change runtime behavior.
- Do not overwrite unrelated in-progress changes.

## Impact Scope

- `README.md`
- `pyproject.toml`
- `.aiflow/plan.md`

## Steps

1. Done: Read compact project context, project rules, package metadata, and CLI entry points.
2. Done: Draft root README with overview, install, quick start, commands, boundaries, docs, and release checks.
3. Done: Update package metadata to use the root README.
4. Done: Run verification and review checks.
5. Done: Run local wheel build as a release packaging sanity check.

## Verification

- Passed: `scripts\aiflow-dev.bat verify --auto --continue-on-error`
- Passed: `git diff --check`
- Passed: `scripts\aiflow-dev.bat review`
- Passed: `python -m pip wheel . -w dist`
- Not run: `python -m build --sdist --wheel` because the active Python environment does not have the `build` module installed.

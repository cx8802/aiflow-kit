# Implementation Plan

## Goal

Keep Playwright npm packages and browser downloads in `aiflow-kit`, so target projects can use the shared frontend verification runtime without creating their own `.tools/frontend-tools` or `.tools/ms-playwright`.

## Non-goals

- Do not move unrelated project-local Go, Node, Maven, or cache policy out of target projects.
- Do not change frontend project config, generated project context, or project skill ownership.
- Do not make Playwright a user-global npm install.

## Impact Scope

- `src/aiflow/commands/frontend.py`
- `tests/test_cli_smoke.py`
- frontend install and update instructions in scripts, skills, and docs

## Steps

1. Add regression coverage proving frontend installs target the kit runtime root.
2. Resolve Playwright package and browser directories from `aiflow-kit` instead of the target repository.
3. Stop target-project install guidance from claiming Playwright tooling is copied into each project.
4. Keep quick install and update scripts responsible for preparing the shared runtime.
5. Run repository verification.

## Verification

- `python -m unittest discover -s tests`
- `.\.venv\Scripts\aiflow.exe verify --auto`
- `.\.venv\Scripts\python.exe -m compileall src`

## Risks

- Existing docs and skills may still imply a target project owns `.tools/frontend-tools`.
- Callers that invoke `aiflow frontend install` from another repository must still see a usable shared runtime path.
- Browser downloads remain potentially slow the first time the shared runtime is prepared.

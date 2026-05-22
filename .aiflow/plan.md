# Plan

Update project description, publish it to Gitee, and prepare project self-recommendation.

## Goal

- Align README, package metadata, and Gitee repository sidebar description.
- Commit the description update and push it to the Gitee remote.
- Try to complete the Gitee project self-recommendation flow; if it requires an authenticated web form, provide a ready-to-submit recommendation draft.

## Non-goals

- Do not store or commit access tokens.
- Do not include unrelated local database or docs drafts.
- Do not create a new release tag for a description-only update.

## Impact Scope

- `README.md`
- `pyproject.toml`
- `.aiflow/plan.md`
- Gitee repository metadata for `aoxianglantian/aiflow-kit`

## Steps

1. Done: Read compact project context and inspect working tree.
2. Done: Update README and package description.
3. Done: Verify local changes.
4. Done: Update Gitee repository description via API.
5. Done: Commit and push to `master`.
6. Done: Confirm Gitee self-recommendation requires the logged-in GVP web form and prepare a submission draft.

## Verification

- Passed: `git diff --check`
- Passed: `scripts\aiflow-dev.bat verify --auto --continue-on-error`

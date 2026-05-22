# Plan

Create a GitHub repository and push the current project code to it.

## Goal

- Create `aiflow-kit` under the target GitHub owner.
- Add a GitHub remote alongside the existing Gitee `origin`.
- Push `master` and tags to GitHub.

## Non-goals

- Do not store GitHub tokens in files, memory, or git config.
- Do not include unrelated untracked local files.
- Do not change the existing Gitee remote.

## Impact Scope

- GitHub repository metadata.
- Local git remotes.
- `.aiflow/plan.md`

## Steps

1. Done: Read compact project context and inspect working tree.
2. Done: Check local GitHub tooling and credentials.
3. Done: GitHub CLI is unavailable; switch to Chrome plugin and browser login.
4. Done: Confirm `cx8802/aiflow-kit` already exists as an empty public GitHub repository.
5. In progress: Add GitHub remote and push `master` plus tags.

## Verification

- Pending: confirm GitHub remote exists and `master` plus tags are pushed.

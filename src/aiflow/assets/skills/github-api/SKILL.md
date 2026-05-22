---
name: github-api
description: Use when the user asks Codex to operate GitHub, github.com, a GitHub remote repository, GitHub Releases, GitHub Issues, GitHub Pull Requests, or GitHub REST API automation, especially when using the local aiflow forge CLI for repository detection or release creation.
---

# GitHub API

## Preferred Path

Use the local aiflow automation command when available:

```bat
aiflow forge detect
aiflow forge release create --provider github --repo <owner>/<repo> --tag vX.Y.Z --name vX.Y.Z --notes "Release notes"
aiflow forge release get --provider github --repo <owner>/<repo> --tag vX.Y.Z
```

For a source checkout where `aiflow` is not on `PATH`, use:

```bat
{{ AIFLOW_DEV_BAT }} forge detect
```

Use direct Git commands for normal branch and tag work:

```bat
git fetch origin
git status --short --branch
git push origin <branch>
git push origin <tag>
```

## API Reference

For endpoint tables, request bodies, and direct REST examples, read [references/api-reference.md](references/api-reference.md) when the task needs GitHub API calls beyond simple Git pushes or `aiflow forge release`.

## Token Safety

- Prefer `GITHUB_TOKEN`; `GH_TOKEN` is also accepted by `aiflow forge`.
- Never write tokens to tracked files, README, logs, memory files, or final answers.
- Do not put tokens in command arguments when an environment variable works.
- If a token was pasted in chat or logs, recommend revoking and regenerating it.

## Release Workflow

1. Verify the repository and tag:

```bat
aiflow forge detect
git tag --list vX.Y.Z
git ls-remote --tags origin vX.Y.Z
```

2. Dry-run the API request:

```bat
aiflow forge release create --provider github --repo <owner>/<repo> --tag vX.Y.Z --name vX.Y.Z --notes "Release notes" --dry-run
```

3. Create the GitHub Release:

```bat
aiflow forge release create --provider github --repo <owner>/<repo> --tag vX.Y.Z --name vX.Y.Z --notes "Release notes"
```

4. Confirm it exists:

```bat
aiflow forge release get --provider github --repo <owner>/<repo> --tag vX.Y.Z
```

## Direct API Shape

GitHub REST release creation uses:

```text
POST https://api.github.com/repos/<owner>/<repo>/releases
```

Headers:

```text
Accept: application/vnd.github+json
Authorization: Bearer <token>
X-GitHub-Api-Version: 2022-11-28
```

Body fields include:

```json
{
  "tag_name": "vX.Y.Z",
  "target_commitish": "main",
  "name": "vX.Y.Z",
  "body": "Release notes",
  "draft": false,
  "prerelease": false
}
```

## Failure Handling

- For `401` or `403`, check token validity and scopes first.
- For `404`, check owner/repo, private repository access, and whether the token can read the repository.
- For secondary rate limits, wait and retry later instead of looping.
- Report API failures with status and message only; never echo the token.

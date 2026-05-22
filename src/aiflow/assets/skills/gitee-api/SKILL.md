---
name: gitee-api
description: Use when the user asks Codex to operate Gitee, gitee.com, 码云, or a Gitee remote repository, including creating or updating Gitee releases, publishing tags, managing issues, pull requests, comments, repository metadata, checking Gitee remote status, or calling Gitee OpenAPI v5 with a personal access token.
---

# Gitee API

## Scope

Use Git for normal repository actions:

```bat
git remote -v
git fetch origin
git status --short --branch
git push origin <branch>
git push origin <tag>
```

Use Gitee OpenAPI only when Git is not enough, such as releases, issues, pull requests, comments, labels, webhooks, repository metadata, or user/org lookups.

## Safety

- Treat Gitee as a China-hosted service; prefer direct network access and do not enable overseas proxy by default.
- Never write personal access tokens to tracked files, README, logs, `.aiflow/memory.md`, or final answers.
- Prefer `GITEE_ACCESS_TOKEN` for API calls. If a persistent project-local token is explicitly needed, use an ignored local file such as `.aiflow/gitee.local.toml`.
- Before mutating Gitee state, inspect the target repository, branch, tag, issue, pull request, or release.
- For destructive actions such as deleting tags, branches, releases, comments, hooks, or issues, ask for explicit confirmation unless the user gave an unambiguous instruction.
- In final answers, report object ids, tag names, URLs, and status; do not echo tokens or full authenticated URLs.

## Repository Detection

When the user does not provide owner/repo, infer it from the current Git remote:

```bat
git remote get-url origin
```

Parse common Gitee forms:

```text
https://gitee.com/<owner>/<repo>.git
git@gitee.com:<owner>/<repo>.git
```

Use the repo path without the trailing `.git` as `<owner>/<repo>`.

## API Basics

Base URL:

```text
https://gitee.com/api/v5
```

Authentication normally uses the `access_token` parameter. Prefer passing it from the environment inside the current shell command:

```bat
curl -sS "https://gitee.com/api/v5/user?access_token=%GITEE_ACCESS_TOKEN%"
```

In PowerShell:

```powershell
$token = $env:GITEE_ACCESS_TOKEN
Invoke-RestMethod -Method Get -Uri "https://gitee.com/api/v5/user?access_token=$token"
```

If `GITEE_ACCESS_TOKEN` is missing and an API mutation is required, ask the user to provide or configure a token. Do not guess or search local files for secrets.

## Common Workflows

### Publish Git Branch And Tag

1. Run verification first when the repository has configured checks.
2. Confirm `git status --short --branch` and `git log --oneline --decorate -3`.
3. Push branch:

```bat
git push origin <branch>
```

4. Create and push annotated tag when requested:

```bat
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

### Create A Gitee Release

Use this after the tag exists on Gitee. Prefer `multipart/form-data` or form fields because many Gitee v5 endpoints document form parameters.

```powershell
$token = $env:GITEE_ACCESS_TOKEN
$owner = "<owner>"
$repo = "<repo>"
$body = @{
  access_token = $token
  tag_name = "vX.Y.Z"
  name = "vX.Y.Z"
  body = "Release notes"
  prerelease = "false"
}
Invoke-RestMethod -Method Post -Uri "https://gitee.com/api/v5/repos/$owner/$repo/releases" -Form $body
```

If the endpoint rejects `-Form` in the current PowerShell version, use `curl.exe -F` instead:

```bat
curl.exe -sS -X POST ^
  -F "access_token=%GITEE_ACCESS_TOKEN%" ^
  -F "tag_name=vX.Y.Z" ^
  -F "name=vX.Y.Z" ^
  -F "body=Release notes" ^
  -F "prerelease=false" ^
  "https://gitee.com/api/v5/repos/<owner>/<repo>/releases"
```

### List Or Inspect Releases

```bat
curl.exe -sS "https://gitee.com/api/v5/repos/<owner>/<repo>/releases?access_token=%GITEE_ACCESS_TOKEN%"
```

```bat
curl.exe -sS "https://gitee.com/api/v5/repos/<owner>/<repo>/releases/tags/vX.Y.Z?access_token=%GITEE_ACCESS_TOKEN%"
```

### Manage Issues

List repository issues:

```bat
curl.exe -sS "https://gitee.com/api/v5/repos/<owner>/<repo>/issues?state=open&access_token=%GITEE_ACCESS_TOKEN%"
```

Create an issue:

```bat
curl.exe -sS -X POST ^
  -F "access_token=%GITEE_ACCESS_TOKEN%" ^
  -F "title=Issue title" ^
  -F "body=Issue body" ^
  "https://gitee.com/api/v5/repos/<owner>/issues?repo=<repo>"
```

Comment on an issue:

```bat
curl.exe -sS -X POST ^
  -F "access_token=%GITEE_ACCESS_TOKEN%" ^
  -F "body=Comment body" ^
  "https://gitee.com/api/v5/repos/<owner>/<repo>/issues/<number>/comments"
```

### Manage Pull Requests

List pull requests:

```bat
curl.exe -sS "https://gitee.com/api/v5/repos/<owner>/<repo>/pulls?state=open&access_token=%GITEE_ACCESS_TOKEN%"
```

Create a pull request only after confirming source and target branches:

```bat
curl.exe -sS -X POST ^
  -F "access_token=%GITEE_ACCESS_TOKEN%" ^
  -F "title=PR title" ^
  -F "head=<source-branch>" ^
  -F "base=<target-branch>" ^
  -F "body=PR body" ^
  "https://gitee.com/api/v5/repos/<owner>/<repo>/pulls"
```

## Response Handling

- Prefer JSON output and summarize only the fields the user needs.
- For API failures, report HTTP status, Gitee message, endpoint, and whether the token was present, without printing the token.
- If rate limits, permission errors, protected branch rules, or missing repository permissions block the task, stop and explain the blocker.
- If the user asks for a release URL, construct it from the repository path and tag only after confirming the release exists:

```text
https://gitee.com/<owner>/<repo>/releases/tag/<tag>
```

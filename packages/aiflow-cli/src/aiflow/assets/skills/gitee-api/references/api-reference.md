# Gitee OpenAPI v5 Reference

Use this reference when a task requires direct Gitee API calls. Prefer `aiflow forge` for supported release automation.

Base URL:

```text
https://gitee.com/api/v5
```

Token:

```text
GITEE_ACCESS_TOKEN
```

Preferred auth for JSON calls:

```text
Authorization: Bearer <token>
Accept: application/json
Content-Type: application/json; charset=utf-8
```

Some older Gitee examples use `access_token` as a query/form parameter. Prefer bearer auth first; fall back to `access_token` only when an endpoint rejects bearer auth.

## Repository

| Action | Method | Endpoint | Notes |
| --- | --- | --- | --- |
| Get repository | `GET` | `/repos/{owner}/{repo}` | Reads metadata such as `description`, `default_branch`, permissions |
| Update repository | `PATCH` | `/repos/{owner}/{repo}` | Body requires `name`; supports `description`, `homepage`, `default_branch`, issue/wiki/PR settings |
| List tags | `GET` | `/repos/{owner}/{repo}/tags` | Confirms whether a pushed Git tag exists |
| Create tag | `POST` | `/repos/{owner}/{repo}/tags` | Prefer Git tag + `git push origin <tag>` unless API creation is required |

Update repository body:

```json
{
  "name": "repo-name",
  "description": "Repository description",
  "homepage": "https://example.com",
  "default_branch": "master"
}
```

## Releases

| Action | Method | Endpoint | Notes |
| --- | --- | --- | --- |
| List releases | `GET` | `/repos/{owner}/{repo}/releases` | Use to check whether the release panel is empty |
| Get release | `GET` | `/repos/{owner}/{repo}/releases/{id}` | Lookup by numeric release id |
| Get release by tag | `GET` | `/repos/{owner}/{repo}/releases/tags/{tag}` | Best post-create verification |
| Create release | `POST` | `/repos/{owner}/{repo}/releases` | Use after tag exists |
| Update release | `PATCH` | `/repos/{owner}/{repo}/releases/{id}` | Update name/body/prerelease |
| Delete release | `DELETE` | `/repos/{owner}/{repo}/releases/{id}` | Destructive; require explicit confirmation |
| Upload asset | `POST` | `/repos/{owner}/{repo}/releases/{release_id}/attach_files` | Multipart upload |
| List assets | `GET` | `/repos/{owner}/{repo}/releases/{release_id}/attach_files` | Release attachments |
| Delete asset | `DELETE` | `/repos/{owner}/{repo}/releases/{release_id}/attach_files/{attach_file_id}` | Destructive |

Create release body. Gitee SDK names these fields `tagName` and `targetCommitish`, but JSON calls have worked with `snake_case`; `aiflow forge` uses `snake_case`.

```json
{
  "tag_name": "v1.0.0",
  "target_commitish": "master",
  "name": "v1.0.0",
  "body": "Release notes",
  "prerelease": false
}
```

PowerShell-safe direct call:

```powershell
$token = $env:GITEE_ACCESS_TOKEN
$headers = @{ Authorization = "Bearer $token"; Accept = "application/json" }
$body = @{
  tag_name = "v1.0.0"
  target_commitish = "master"
  name = "v1.0.0"
  body = "Release notes"
  prerelease = $false
} | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "https://gitee.com/api/v5/repos/<owner>/<repo>/releases" -Headers $headers -Body ([Text.Encoding]::UTF8.GetBytes($body)) -ContentType "application/json; charset=utf-8"
```

## Issues

| Action | Method | Endpoint | Notes |
| --- | --- | --- | --- |
| List repository issues | `GET` | `/repos/{owner}/{repo}/issues` | Filters include `state`, `labels`, `sort`, `direction`, `page`, `per_page` |
| Get issue | `GET` | `/repos/{owner}/{repo}/issues/{number}` | `number` is the issue number without `#` |
| Create issue | `POST` | `/repos/{owner}/issues` | Body must include target `repo` |
| Update issue | `PATCH` | `/repos/{owner}/issues/{number}` | Updates title/body/state/assignee fields |
| List issue comments | `GET` | `/repos/{owner}/{repo}/issues/{number}/comments` | Supports pagination |
| Create issue comment | `POST` | `/repos/{owner}/{repo}/issues/{number}/comments` | Body contains `body` |
| Update issue comment | `PATCH` | `/repos/{owner}/{repo}/issues/comments/{id}` | Comment id, not issue number |
| Delete issue comment | `DELETE` | `/repos/{owner}/{repo}/issues/comments/{id}` | Destructive |

Create issue body:

```json
{
  "repo": "repo-name",
  "title": "Issue title",
  "body": "Issue body",
  "labels": "bug,help wanted"
}
```

Create issue comment body:

```json
{
  "body": "Comment body"
}
```

## Pull Requests

| Action | Method | Endpoint | Notes |
| --- | --- | --- | --- |
| List pull requests | `GET` | `/repos/{owner}/{repo}/pulls` | Filters include `state`, `head`, `base`, `sort`, `direction`, `page`, `per_page` |
| Get pull request | `GET` | `/repos/{owner}/{repo}/pulls/{number}` | `number` is PR number |
| Create pull request | `POST` | `/repos/{owner}/{repo}/pulls` | Requires `head`, `base`, `title` |
| Update pull request | `PATCH` | `/repos/{owner}/{repo}/pulls/{number}` | Update title/body/state/base |
| List commits | `GET` | `/repos/{owner}/{repo}/pulls/{number}/commits` | Gitee caps displayed commit count |
| List changed files | `GET` | `/repos/{owner}/{repo}/pulls/{number}/files` | Gitee caps diff file count |
| List comments | `GET` | `/repos/{owner}/{repo}/pulls/{number}/comments` | PR discussion comments |
| Create comment | `POST` | `/repos/{owner}/{repo}/pulls/{number}/comments` | Body contains comment fields |
| Merge PR | `PUT` | `/repos/{owner}/{repo}/pulls/{number}/merge` | Destructive; require explicit confirmation |

Create pull request body:

```json
{
  "title": "Pull request title",
  "head": "feature-branch",
  "base": "master",
  "body": "Pull request body"
}
```

## Error Handling

- `400`: usually invalid body or field naming; retry with documented body fields and UTF-8 JSON.
- `401`: missing or invalid token.
- `403`: token lacks repository permission or repository is protected.
- `404`: wrong `owner/repo`, private repo access missing, or object does not exist.
- Gitee sometimes returns an empty error body; include method, endpoint, HTTP status, and whether a token was present, but never print the token.

## Sources

- Gitee API v5 Swagger: https://gitee.com/api/v5/swagger
- Gitee SDK docs: https://gitee.com/sdk/gitee5j

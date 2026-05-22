# GitHub REST API Reference

Use this reference when a task requires direct GitHub API calls. Prefer `aiflow forge` for supported release automation.

Base URL:

```text
https://api.github.com
```

Token:

```text
GITHUB_TOKEN
GH_TOKEN
```

Standard headers:

```text
Accept: application/vnd.github+json
Authorization: Bearer <token>
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

## Repository

| Action | Method | Endpoint | Notes |
| --- | --- | --- | --- |
| Get repository | `GET` | `/repos/{owner}/{repo}` | Reads metadata, topics, permissions, default branch |
| Update repository | `PATCH` | `/repos/{owner}/{repo}` | Requires admin or suitable fine-grained token permissions |
| List tags | `GET` | `/repos/{owner}/{repo}/tags` | Confirms tag visibility |
| List releases | `GET` | `/repos/{owner}/{repo}/releases` | Also covered below |
| Replace topics | `PUT` | `/repos/{owner}/{repo}/topics` | Requires preview-compatible headers historically; current JSON works with standard GitHub headers |

Update repository body:

```json
{
  "name": "repo-name",
  "description": "Repository description",
  "homepage": "https://example.com",
  "has_issues": true,
  "has_wiki": true,
  "default_branch": "main"
}
```

Replace topics body:

```json
{
  "names": ["ai", "codex", "cli", "automation"]
}
```

## Releases

| Action | Method | Endpoint | Notes |
| --- | --- | --- | --- |
| List releases | `GET` | `/repos/{owner}/{repo}/releases` | Paginated |
| Get release | `GET` | `/repos/{owner}/{repo}/releases/{release_id}` | Numeric release id |
| Get release by tag | `GET` | `/repos/{owner}/{repo}/releases/tags/{tag}` | Best post-create verification |
| Get latest release | `GET` | `/repos/{owner}/{repo}/releases/latest` | Latest non-draft, non-prerelease release |
| Create release | `POST` | `/repos/{owner}/{repo}/releases` | Requires push/write access |
| Update release | `PATCH` | `/repos/{owner}/{repo}/releases/{release_id}` | Update tag/name/body/draft/prerelease |
| Delete release | `DELETE` | `/repos/{owner}/{repo}/releases/{release_id}` | Destructive |
| Upload asset | `POST` | upload URL from release response | Use `uploads.github.com`; URL template contains `{?name,label}` |
| Delete asset | `DELETE` | `/repos/{owner}/{repo}/releases/assets/{asset_id}` | Destructive |

Create release body:

```json
{
  "tag_name": "v1.0.0",
  "target_commitish": "main",
  "name": "v1.0.0",
  "body": "Release notes",
  "draft": false,
  "prerelease": false,
  "generate_release_notes": false
}
```

## Issues

| Action | Method | Endpoint | Notes |
| --- | --- | --- | --- |
| List repository issues | `GET` | `/repos/{owner}/{repo}/issues` | Includes pull requests unless filtered by response fields |
| Get issue | `GET` | `/repos/{owner}/{repo}/issues/{issue_number}` | Issue numbers are repository-local |
| Create issue | `POST` | `/repos/{owner}/{repo}/issues` | Requires issue write permission |
| Update issue | `PATCH` | `/repos/{owner}/{repo}/issues/{issue_number}` | Update title/body/state/labels/assignees |
| List comments | `GET` | `/repos/{owner}/{repo}/issues/{issue_number}/comments` | Paginated |
| Create comment | `POST` | `/repos/{owner}/{repo}/issues/{issue_number}/comments` | Body contains `body` |
| Update comment | `PATCH` | `/repos/{owner}/{repo}/issues/comments/{comment_id}` | Comment id, not issue number |
| Delete comment | `DELETE` | `/repos/{owner}/{repo}/issues/comments/{comment_id}` | Destructive |

Create issue body:

```json
{
  "title": "Issue title",
  "body": "Issue body",
  "labels": ["bug", "help wanted"],
  "assignees": ["octocat"]
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
| List pull requests | `GET` | `/repos/{owner}/{repo}/pulls` | Filters include `state`, `head`, `base`, `sort`, `direction` |
| Get pull request | `GET` | `/repos/{owner}/{repo}/pulls/{pull_number}` | PR number is repository-local |
| Create pull request | `POST` | `/repos/{owner}/{repo}/pulls` | Requires `head`, `base`, `title` |
| Update pull request | `PATCH` | `/repos/{owner}/{repo}/pulls/{pull_number}` | Update title/body/state/base/maintainer edits |
| List commits | `GET` | `/repos/{owner}/{repo}/pulls/{pull_number}/commits` | Paginated |
| List files | `GET` | `/repos/{owner}/{repo}/pulls/{pull_number}/files` | Paginated |
| Check merged | `GET` | `/repos/{owner}/{repo}/pulls/{pull_number}/merge` | Returns 204 if merged |
| Merge PR | `PUT` | `/repos/{owner}/{repo}/pulls/{pull_number}/merge` | Destructive; require explicit confirmation |

Create pull request body:

```json
{
  "title": "Pull request title",
  "head": "feature-branch",
  "base": "main",
  "body": "Pull request body",
  "draft": false,
  "maintainer_can_modify": true
}
```

Important: review comments and line comments use separate pull request review endpoints; ordinary discussion on a PR is usually an issue comment because GitHub PRs are also issues.

## Error Handling

- `401`: missing, expired, or invalid token.
- `403`: insufficient scope, SSO authorization needed, rate limit, or secondary rate limit.
- `404`: wrong `owner/repo`, private repo access missing, or hidden object due to insufficient permissions.
- `422`: validation failed, often missing `head`/`base`, duplicate PR, invalid tag, or malformed body.
- Report status, endpoint, GitHub `message`, and `documentation_url`; never print tokens.

## Sources

- GitHub REST API docs: https://docs.github.com/en/rest
- Releases: https://docs.github.com/en/rest/releases/releases
- Repositories: https://docs.github.com/en/rest/repos/repos
- Issues: https://docs.github.com/en/rest/issues/issues
- Pull requests: https://docs.github.com/en/rest/pulls/pulls

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


PROVIDERS = {"gitee", "github"}
DEFAULT_API_BASE = {
    "gitee": "https://gitee.com/api/v5",
    "github": "https://api.github.com",
}
DEFAULT_TOKEN_ENV = {
    "gitee": "GITEE_ACCESS_TOKEN",
    "github": "GITHUB_TOKEN",
}


@dataclass(frozen=True)
class ForgeRepo:
    provider: str
    owner: str
    repo: str
    remote_url: str = ""


@dataclass(frozen=True)
class ForgeRequest:
    provider: str
    method: str
    url: str
    headers: dict[str, str]
    body: dict[str, Any] | None = None


@dataclass(frozen=True)
class ForgeResponse:
    status: int
    body: str
    data: Any


class ForgeError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


def parse_remote_url(url: str) -> ForgeRepo | None:
    value = url.strip()
    patterns = [
        r"^https?://(?P<host>github\.com|gitee\.com)/(?P<owner>[^/]+)/(?P<repo>[^/#?]+?)(?:\.git)?/?$",
        r"^git@(?P<host>github\.com|gitee\.com):(?P<owner>[^/]+)/(?P<repo>[^/#?]+?)(?:\.git)?$",
        r"^ssh://git@(?P<host>github\.com|gitee\.com)/(?P<owner>[^/]+)/(?P<repo>[^/#?]+?)(?:\.git)?/?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, value)
        if not match:
            continue
        host = match.group("host")
        provider = "github" if host == "github.com" else "gitee"
        return ForgeRepo(provider=provider, owner=match.group("owner"), repo=match.group("repo"), remote_url=value)
    return None


def parse_repo_slug(provider: str, slug: str) -> ForgeRepo:
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported forge provider: {provider}")
    parts = slug.strip().strip("/").split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("Repository must be in owner/repo format")
    repo = parts[1][:-4] if parts[1].endswith(".git") else parts[1]
    return ForgeRepo(provider=provider, owner=parts[0], repo=repo)


def release_create_request(
    repo: ForgeRepo,
    *,
    token: str,
    tag: str,
    name: str,
    notes: str,
    target: str = "",
    prerelease: bool = False,
    draft: bool = False,
    api_base_url: str | None = None,
) -> ForgeRequest:
    base = (api_base_url or DEFAULT_API_BASE[repo.provider]).rstrip("/")
    url = f"{base}/repos/{repo.owner}/{repo.repo}/releases"
    body: dict[str, Any] = {
        "tag_name": tag,
        "name": name or tag,
        "body": notes,
        "prerelease": prerelease,
    }
    if target:
        body["target_commitish"] = target
    if repo.provider == "github":
        body["draft"] = draft
        return ForgeRequest(
            provider=repo.provider,
            method="POST",
            url=url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
            body=body,
        )
    if draft:
        raise ValueError("Gitee releases do not support draft releases through this command")
    return ForgeRequest(
        provider=repo.provider,
        method="POST",
        url=url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        body=body,
    )


def release_get_request(repo: ForgeRepo, *, token: str, tag: str, api_base_url: str | None = None) -> ForgeRequest:
    base = (api_base_url or DEFAULT_API_BASE[repo.provider]).rstrip("/")
    url = f"{base}/repos/{repo.owner}/{repo.repo}/releases/tags/{tag}"
    if repo.provider == "github":
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    else:
        headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    return ForgeRequest(provider=repo.provider, method="GET", url=url, headers=headers)


def invoke_forge_request(request: ForgeRequest, *, timeout: int = 20) -> ForgeResponse:
    body_bytes = None
    if request.body is not None:
        body_bytes = json.dumps(request.body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(request.url, data=body_bytes, headers=request.headers, method=request.method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            text = response.read().decode("utf-8")
            return ForgeResponse(status=response.status, body=text, data=_parse_json(text))
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        message = f"Forge API request failed with HTTP {exc.code}"
        raise ForgeError(message, status=exc.code, body=text) from exc
    except urllib.error.URLError as exc:
        raise ForgeError(f"Forge API request failed: {exc.reason}") from exc


def redacted_request(request: ForgeRequest) -> dict[str, Any]:
    headers = dict(request.headers)
    if "Authorization" in headers:
        headers["Authorization"] = "***"
    return {
        "provider": request.provider,
        "method": request.method,
        "url": request.url,
        "headers": headers,
        "body": request.body,
    }


def _parse_json(text: str) -> Any:
    if not text.strip():
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text

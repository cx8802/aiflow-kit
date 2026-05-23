from __future__ import annotations

import json
import os
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from ..core.forge import (
    DEFAULT_TOKEN_ENV,
    ForgeError,
    ForgeRepo,
    forge_local_path,
    invoke_forge_request,
    load_forge_auth,
    parse_remote_url,
    parse_repo_slug,
    redacted_request,
    release_create_request,
    release_get_request,
    remove_forge_token,
    save_forge_token,
)
from ..core.paths import project_root


def configure_forge_parser(sub) -> None:
    forge = sub.add_parser("forge", help="Automate Gitee and GitHub repository workflows")
    forge_sub = forge.add_subparsers(dest="forge_command", required=True)

    detect = forge_sub.add_parser("detect", help="Detect Gitee/GitHub provider from a Git remote")
    detect.add_argument("--remote", default="origin", help="Git remote name. Default: origin")
    detect.add_argument("--format", choices=["text", "json"], default="text")
    detect.set_defaults(func=run_forge)

    auth = forge_sub.add_parser("auth", help="Configure local Gitee/GitHub access tokens")
    auth_sub = auth.add_subparsers(dest="auth_command", required=True)

    auth_set = auth_sub.add_parser("set", help="Store a provider token in .aiflow/forge.local.toml")
    auth_set.add_argument("--provider", choices=["gitee", "github"], required=True)
    auth_set.add_argument("--from-env", default="", help="Read token from this environment variable")
    auth_set.add_argument("--token-stdin", action="store_true", help="Read token from standard input")
    auth_set.set_defaults(func=run_forge)

    auth_status = auth_sub.add_parser("status", help="Show whether forge tokens are configured")
    auth_status.add_argument("--provider", choices=["all", "gitee", "github"], default="all")
    auth_status.set_defaults(func=run_forge)

    auth_unset = auth_sub.add_parser("unset", help="Remove a provider token from .aiflow/forge.local.toml")
    auth_unset.add_argument("--provider", choices=["gitee", "github"], required=True)
    auth_unset.set_defaults(func=run_forge)

    release = forge_sub.add_parser("release", help="Automate Gitee/GitHub releases")
    release_sub = release.add_subparsers(dest="release_command", required=True)

    create = release_sub.add_parser("create", help="Create a Gitee or GitHub release")
    add_release_common_args(create)
    create.add_argument("--notes", default="", help="Release notes text")
    create.add_argument("--notes-file", type=Path, default=None, help="Read release notes from a file")
    create.add_argument("--target", default="", help="Target branch or commit SHA")
    create.add_argument("--prerelease", action="store_true", help="Mark release as prerelease")
    create.add_argument("--draft", action="store_true", help="Create a GitHub draft release")
    create.add_argument("--dry-run", action="store_true", help="Print the redacted API request without sending it")
    create.set_defaults(func=run_forge)

    get = release_sub.add_parser("get", help="Get a Gitee or GitHub release by tag")
    add_release_common_args(get, require_name=False)
    get.set_defaults(func=run_forge)


def add_release_common_args(parser, *, require_name: bool = True) -> None:
    parser.add_argument("--provider", choices=["auto", "gitee", "github"], default="auto")
    parser.add_argument("--remote", default="origin", help="Git remote name for provider/repo detection")
    parser.add_argument("--repo", default="", help="Repository as owner/repo")
    parser.add_argument("--tag", required=True, help="Release tag")
    if require_name:
        parser.add_argument("--name", default="", help="Release name. Defaults to --tag")
    parser.add_argument("--token-env", default="", help="Token environment variable override")
    parser.add_argument("--api-base-url", default="", help="Override API base URL for tests or enterprise hosts")
    parser.add_argument("--timeout", type=int, default=20)


def run_forge(args: Namespace) -> int:
    if args.forge_command == "detect":
        return forge_detect(args)
    if args.forge_command == "auth":
        if args.auth_command == "set":
            return forge_auth_set(args)
        if args.auth_command == "status":
            return forge_auth_status(args)
        if args.auth_command == "unset":
            return forge_auth_unset(args)
    if args.forge_command == "release":
        if args.release_command == "create":
            return forge_release_create(args)
        if args.release_command == "get":
            return forge_release_get(args)
    raise ValueError("Unknown forge command")


def forge_detect(args: Namespace) -> int:
    try:
        repo = detect_repo(args.remote)
    except ValueError as exc:
        print(str(exc))
        return 2
    payload = repo_json(repo)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{repo.provider}: {repo.owner}/{repo.repo}")
    return 0


def forge_release_create(args: Namespace) -> int:
    try:
        repo = resolve_repo(args.provider, args.repo, args.remote)
        notes = read_notes(args.notes, args.notes_file)
        token, _, expected_token_env = resolve_token(repo.provider, args.token_env)
        if not token and not args.dry_run:
            print(f"Missing token environment variable or local forge token: {expected_token_env}")
            print(f"Run: aiflow forge auth set --provider {repo.provider} --from-env {expected_token_env}")
            return 2
        request = release_create_request(
            repo,
            token=token or "dry-run-token",
            tag=args.tag,
            name=args.name or args.tag,
            notes=notes,
            target=args.target,
            prerelease=bool(args.prerelease),
            draft=bool(args.draft),
            api_base_url=args.api_base_url or None,
        )
        if args.dry_run:
            print(json.dumps(redacted_request(request), ensure_ascii=False, indent=2))
            return 0
        response = invoke_forge_request(request, timeout=args.timeout)
    except (ValueError, ForgeError) as exc:
        print_error(exc)
        return 2 if isinstance(exc, ValueError) else 1
    print(json.dumps(response.data, ensure_ascii=False, indent=2))
    return 0


def forge_release_get(args: Namespace) -> int:
    try:
        repo = resolve_repo(args.provider, args.repo, args.remote)
        token, _, expected_token_env = resolve_token(repo.provider, args.token_env)
        if not token:
            print(f"Missing token environment variable or local forge token: {expected_token_env}")
            print(f"Run: aiflow forge auth set --provider {repo.provider} --from-env {expected_token_env}")
            return 2
        request = release_get_request(repo, token=token, tag=args.tag, api_base_url=args.api_base_url or None)
        response = invoke_forge_request(request, timeout=args.timeout)
    except (ValueError, ForgeError) as exc:
        print_error(exc)
        return 2 if isinstance(exc, ValueError) else 1
    print(json.dumps(response.data, ensure_ascii=False, indent=2))
    return 0


def forge_auth_set(args: Namespace) -> int:
    try:
        root = project_root()
        token = read_auth_token(args.provider, args.from_env, bool(args.token_stdin))
        path = save_forge_token(root, args.provider, token)
    except ValueError as exc:
        print(str(exc))
        return 2
    print(f"{args.provider}: configured {path}")
    return 0


def forge_auth_status(args: Namespace) -> int:
    providers = ["gitee", "github"] if args.provider == "all" else [args.provider]
    for provider in providers:
        token, source, expected_env = resolve_token(provider, "")
        if token:
            print(f"{provider}: configured ({source})")
        else:
            print(f"{provider}: missing (set {expected_env} or run forge auth set)")
    return 0


def forge_auth_unset(args: Namespace) -> int:
    try:
        path = remove_forge_token(project_root(), args.provider)
    except ValueError as exc:
        print(str(exc))
        return 2
    print(f"{args.provider}: removed from {path}")
    return 0


def resolve_repo(provider: str, repo_slug: str, remote: str) -> ForgeRepo:
    if repo_slug:
        if provider == "auto":
            raise ValueError("--repo requires --provider gitee or --provider github")
        return parse_repo_slug(provider, repo_slug)
    repo = detect_repo(remote)
    if provider != "auto" and repo.provider != provider:
        return ForgeRepo(provider=provider, owner=repo.owner, repo=repo.repo, remote_url=repo.remote_url)
    return repo


def detect_repo(remote: str) -> ForgeRepo:
    root = project_root()
    result = subprocess.run(["git", "remote", "get-url", remote], cwd=root, text=True, capture_output=True)
    if result.returncode != 0:
        raise ValueError(f"Unable to read Git remote: {remote}")
    repo = parse_remote_url(result.stdout.strip())
    if not repo:
        raise ValueError(f"Unsupported Git remote URL: {result.stdout.strip()}")
    return repo


def read_notes(notes: str, notes_file: Path | None) -> str:
    if notes_file:
        return notes_file.read_text(encoding="utf-8")
    return notes


def read_auth_token(provider: str, from_env: str, token_stdin: bool) -> str:
    if token_stdin:
        token = sys.stdin.read().strip()
        if not token:
            raise ValueError("Token read from stdin is empty")
        return token
    env_name = token_env_name(provider, from_env)
    token = os.environ.get(env_name, "")
    if not token:
        raise ValueError(f"Missing token environment variable: {env_name}")
    return token


def resolve_token(provider: str, override: str) -> tuple[str, str, str]:
    root = project_root()
    env_names = token_env_candidates(provider, override)
    for env_name in env_names:
        token = os.environ.get(env_name, "")
        if token:
            return token, f"env:{env_name}", env_names[0]
    if not override:
        local_token = load_forge_auth(root).get(provider, {}).get("token", "")
        if local_token:
            return local_token, f"local:{forge_local_path(root)}", env_names[0]
    return "", "", env_names[0]


def token_env_candidates(provider: str, override: str) -> list[str]:
    if override:
        return [override]
    if provider == "github":
        return ["GITHUB_TOKEN", "GH_TOKEN"]
    return [DEFAULT_TOKEN_ENV[provider]]


def token_env_name(provider: str, override: str) -> str:
    if override:
        return override
    if provider == "github" and os.environ.get("GITHUB_TOKEN"):
        return "GITHUB_TOKEN"
    if provider == "github" and os.environ.get("GH_TOKEN"):
        return "GH_TOKEN"
    return DEFAULT_TOKEN_ENV[provider]


def repo_json(repo: ForgeRepo) -> dict[str, str]:
    return {"provider": repo.provider, "owner": repo.owner, "repo": repo.repo, "remote_url": repo.remote_url}


def print_error(exc: Exception) -> None:
    print(str(exc))
    if isinstance(exc, ForgeError):
        if exc.status is not None:
            print(f"status: {exc.status}")
        if exc.body:
            print(exc.body)

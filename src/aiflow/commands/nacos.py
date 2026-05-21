from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from ..core.nacos import (
    fetch_nacos_config,
    load_nacos,
    nacos_config_path,
    nacos_local_path,
    redact_profile,
    resolve_nacos_profile,
    save_nacos_file,
)
from ..core.paths import ensure_aiflow_dir, project_root


def configure_nacos_parser(sub) -> None:
    nacos = sub.add_parser("nacos", help="Manage project-level Nacos config-center profiles")
    nacos_sub = nacos.add_subparsers(dest="nacos_command", required=True)

    add = nacos_sub.add_parser("add", help="Add or update a Nacos profile")
    add.add_argument("name")
    add.add_argument("--description", default="")
    add.add_argument("--server", default="", help="Base URL, for example http://127.0.0.1:8848")
    add.add_argument("--scheme", default="http")
    add.add_argument("--host", default="")
    add.add_argument("--port", type=int, default=8848)
    add.add_argument("--namespace", default="", help="Default Nacos namespace/tenant")
    add.add_argument("--username-env", default="")
    add.add_argument("--password-env", default="")
    add.add_argument("--access-token-env", default="")
    add.add_argument("--username", default="", help="Secret username; requires --secret-local")
    add.add_argument("--password", default="", help="Secret password; requires --secret-local")
    add.add_argument("--access-token", default="", help="Secret access token; requires --secret-local")
    add.add_argument("--secret-local", action="store_true", help="Store secrets in .aiflow/nacos.local.toml")
    add.add_argument("--force", action="store_true")
    add.set_defaults(func=run_nacos)

    list_cmd = nacos_sub.add_parser("list", help="List configured Nacos profiles")
    list_cmd.set_defaults(func=run_nacos)

    show = nacos_sub.add_parser("show", help="Show a Nacos profile with secrets redacted")
    show.add_argument("name")
    show.set_defaults(func=run_nacos)

    get = nacos_sub.add_parser("get", help="Fetch config content from Nacos")
    get.add_argument("name")
    get.add_argument("--data-id", required=True)
    get.add_argument("--group", default="DEFAULT_GROUP")
    get.add_argument("--namespace", default="", help="Override profile namespace/tenant")
    get.add_argument("--timeout", type=int, default=10)
    get.add_argument("--format", choices=["text", "json"], default="text")
    get.add_argument("--output", type=Path, default=None, help="Optional output file for config content")
    get.set_defaults(func=run_nacos)


def run_nacos(args: Namespace) -> int:
    command = args.nacos_command
    if command == "add":
        return nacos_add(args)
    if command == "list":
        return nacos_list(args)
    if command == "show":
        return nacos_show(args)
    if command == "get":
        return nacos_get(args)
    raise ValueError(f"Unknown nacos command: {command}")


def nacos_add(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    config, local = load_nacos(root)
    profiles = config.setdefault("nacos", {})
    local_profiles = local.setdefault("nacos", {})

    if args.name in profiles and not args.force:
        print(f"Nacos profile already exists: {args.name}. Use --force to overwrite.")
        return 2

    secrets = {"username": args.username, "password": args.password, "access_token": args.access_token}
    if any(secrets.values()) and not args.secret_local:
        print("Refusing to store Nacos secrets in tracked config. Use --secret-local or env var names.")
        return 2

    profile = {
        "description": args.description,
        "server": args.server,
        "scheme": args.scheme if not args.server else "",
        "host": args.host,
        "port": args.port if not args.server else 0,
        "namespace": args.namespace,
        "username_env": args.username_env,
        "password_env": args.password_env,
        "access_token_env": args.access_token_env,
    }
    profiles[args.name] = {key: value for key, value in profile.items() if value not in ("", 0, None)}
    save_nacos_file(nacos_config_path(root), config)

    if args.secret_local:
        local_profiles[args.name] = {key: value for key, value in secrets.items() if value}
        save_nacos_file(nacos_local_path(root), local)

    print(f"written: {nacos_config_path(root)}")
    if args.secret_local:
        print(f"written: {nacos_local_path(root)}")
    return 0


def nacos_list(args: Namespace) -> int:
    root = project_root()
    config, local = load_nacos(root)
    profiles = config.get("nacos", {})
    if not profiles:
        print("No Nacos profiles configured.")
        return 0
    for name in sorted(profiles):
        profile = profiles[name]
        local_marker = " + local secrets" if name in local.get("nacos", {}) else ""
        target = profile.get("server") or profile.get("host") or ""
        namespace = f" namespace={profile.get('namespace')}" if profile.get("namespace") else ""
        print(f"{name}: {target}{namespace}{local_marker}")
    return 0


def nacos_show(args: Namespace) -> int:
    root = project_root()
    config, local = load_nacos(root)
    profile = config.get("nacos", {}).get(args.name)
    if not profile:
        print(f"Nacos profile not found: {args.name}")
        return 2
    local_profile = local.get("nacos", {}).get(args.name, {})
    print(json.dumps(redact_profile(args.name, profile, local_profile), indent=2, ensure_ascii=False))
    return 0


def nacos_get(args: Namespace) -> int:
    root = project_root()
    profile = resolve_nacos_profile(root, args.name)
    if not profile:
        print(f"Nacos profile not found: {args.name}")
        return 2
    result = fetch_nacos_config(
        profile,
        data_id=args.data_id,
        group=args.group,
        namespace=args.namespace,
        timeout=args.timeout,
    )
    if result.ok and args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result.content, encoding="utf-8", newline="\n")

    if args.format == "json":
        print(json.dumps(_result_json(result, args.output), indent=2, ensure_ascii=False))
    elif result.ok:
        print(result.content)
        if args.output:
            print(f"written: {args.output}")
    else:
        print(result.message)
    return 0 if result.ok else 1


def _result_json(result, output: Path | None) -> dict[str, object]:
    data: dict[str, object] = {"ok": result.ok, "message": result.message, "status": result.status}
    if result.ok:
        data["content"] = result.content
    if output:
        data["output"] = str(output)
    return data

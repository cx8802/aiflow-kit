from __future__ import annotations

from argparse import REMAINDER, Namespace

from ..core.paths import ensure_aiflow_dir, project_root
from ..core.remote import (
    load_ssh,
    preview_command,
    resolve_ssh_profile,
    run_command,
    save_ssh_file,
    ssh_command,
    ssh_config_path,
    ssh_local_path,
    ssh_profile_json,
)


def configure_ssh_parser(sub) -> None:
    ssh = sub.add_parser("ssh", help="Manage project-level SSH profiles and run remote commands")
    ssh_sub = ssh.add_subparsers(dest="ssh_command", required=True)

    add = ssh_sub.add_parser("add", help="Add or update an SSH profile")
    add.add_argument("name")
    add.add_argument("--description", default="")
    add.add_argument("--host", required=True)
    add.add_argument("--user", default="")
    add.add_argument("--port", type=int, default=22)
    add.add_argument("--key-path-env", default="")
    add.add_argument("--password-env", default="")
    add.add_argument("--passphrase-env", default="")
    add.add_argument("--key-path", default="", help="Private key path; requires --secret-local")
    add.add_argument("--password", default="", help="Password metadata; requires --secret-local")
    add.add_argument("--passphrase", default="", help="Key passphrase metadata; requires --secret-local")
    add.add_argument("--option", action="append", default=[], help="OpenSSH option, for example StrictHostKeyChecking=no")
    add.add_argument("--secret-local", action="store_true", help="Store secrets in .aiflow/ssh.local.toml")
    add.add_argument("--force", action="store_true")
    add.set_defaults(func=run_ssh)

    list_cmd = ssh_sub.add_parser("list", help="List configured SSH profiles")
    list_cmd.set_defaults(func=run_ssh)

    show = ssh_sub.add_parser("show", help="Show an SSH profile with secrets redacted")
    show.add_argument("name")
    show.set_defaults(func=run_ssh)

    run = ssh_sub.add_parser("run", help="Run a command on a configured SSH host")
    run.add_argument("name")
    run.add_argument("--dry-run", action="store_true", help="Print command without executing")
    run.add_argument("--timeout", type=int, default=0, help="Optional timeout in seconds")
    run.add_argument("--ssh-arg", action="append", default=[], help="Extra argument passed to ssh before the host")
    run.add_argument("command", nargs=REMAINDER, help="Remote command and arguments")
    run.set_defaults(func=run_ssh)


def run_ssh(args: Namespace) -> int:
    command = args.ssh_command
    if command == "add":
        return ssh_add(args)
    if command == "list":
        return ssh_list(args)
    if command == "show":
        return ssh_show(args)
    if command == "run":
        return ssh_run(args)
    raise ValueError(f"Unknown ssh command: {command}")


def ssh_add(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    config, local = load_ssh(root)
    profiles = config.setdefault("ssh", {})
    local_profiles = local.setdefault("ssh", {})

    if args.name in profiles and not args.force:
        print(f"SSH profile already exists: {args.name}. Use --force to overwrite.")
        return 2

    secrets = {"key_path": args.key_path, "password": args.password, "passphrase": args.passphrase}
    if any(secrets.values()) and not args.secret_local:
        print("Refusing to store SSH secrets in tracked config. Use --secret-local or env var names.")
        return 2

    profile = {
        "description": args.description,
        "host": args.host,
        "user": args.user,
        "port": args.port,
        "key_path_env": args.key_path_env,
        "password_env": args.password_env,
        "passphrase_env": args.passphrase_env,
        "options": args.option,
    }
    profiles[args.name] = {key: value for key, value in profile.items() if value not in ("", 0, None, [])}
    save_ssh_file(ssh_config_path(root), config)

    if args.secret_local:
        local_profiles[args.name] = {key: value for key, value in secrets.items() if value}
        save_ssh_file(ssh_local_path(root), local)

    print(f"written: {ssh_config_path(root)}")
    if args.secret_local:
        print(f"written: {ssh_local_path(root)}")
    return 0


def ssh_list(args: Namespace) -> int:
    root = project_root()
    config, local = load_ssh(root)
    profiles = config.get("ssh", {})
    if not profiles:
        print("No SSH profiles configured.")
        return 0
    for name in sorted(profiles):
        profile = profiles[name]
        local_marker = " + local secrets" if name in local.get("ssh", {}) else ""
        target = profile.get("host", "")
        user = f"{profile.get('user')}@" if profile.get("user") else ""
        port = f":{profile.get('port')}" if profile.get("port") and profile.get("port") != 22 else ""
        print(f"{name}: {user}{target}{port}{local_marker}")
    return 0


def ssh_show(args: Namespace) -> int:
    root = project_root()
    config, local = load_ssh(root)
    profile = config.get("ssh", {}).get(args.name)
    if not profile:
        print(f"SSH profile not found: {args.name}")
        return 2
    local_profile = local.get("ssh", {}).get(args.name, {})
    print(ssh_profile_json(args.name, profile, local_profile))
    return 0


def ssh_run(args: Namespace) -> int:
    root = project_root()
    profile = resolve_ssh_profile(root, args.name)
    if not profile:
        print(f"SSH profile not found: {args.name}")
        return 2
    command = _normalize_run_args(args)
    if not command:
        print("ssh run requires a remote command")
        return 2
    argv = ssh_command(profile, command, extra_args=args.ssh_arg)
    if args.dry_run:
        print(preview_command(argv).display)
        return 0
    result = run_command(argv, timeout=args.timeout or None)
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")
    return result.returncode


def _normalize_run_args(args: Namespace) -> list[str]:
    command = list(args.command)
    if "--dry-run" in command:
        args.dry_run = True
        command.remove("--dry-run")
    if command and command[0] == "--":
        return command[1:]
    return command

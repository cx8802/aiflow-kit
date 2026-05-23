from __future__ import annotations

from argparse import REMAINDER, Namespace

from ..core.remote import executable, preview_command, run_command, wsl_path_command, wsl_run_command


def configure_wsl_parser(sub) -> None:
    wsl = sub.add_parser("wsl", help="Run commands through Windows Subsystem for Linux")
    wsl_sub = wsl.add_subparsers(dest="wsl_command", required=True)

    doctor = wsl_sub.add_parser("doctor", help="Check whether wsl.exe is available")
    doctor.set_defaults(func=run_wsl)

    list_cmd = wsl_sub.add_parser("list", help="List installed WSL distributions")
    list_cmd.add_argument("--verbose", "-v", action="store_true", help="Show WSL verbose distro output")
    list_cmd.set_defaults(func=run_wsl)

    run = wsl_sub.add_parser("run", help="Run a command in WSL")
    run.add_argument("--distro", default="", help="WSL distribution name")
    run.add_argument("--user", default="", help="Linux user")
    run.add_argument("--cwd", default="", help="Working directory inside WSL")
    run.add_argument("--dry-run", action="store_true", help="Print command without executing")
    run.add_argument("command", nargs=REMAINDER, help="Command and arguments to run")
    run.set_defaults(func=run_wsl)

    path = wsl_sub.add_parser("path", help="Convert a path with wslpath")
    direction = path.add_mutually_exclusive_group(required=True)
    direction.add_argument("--to-wsl", action="store_true", help="Convert a Windows path to WSL style")
    direction.add_argument("--to-win", action="store_true", help="Convert a WSL path to Windows style")
    path.add_argument("--distro", default="", help="WSL distribution name")
    path.add_argument("--dry-run", action="store_true", help="Print command without executing")
    path.add_argument("path")
    path.set_defaults(func=run_wsl)


def run_wsl(args: Namespace) -> int:
    command = args.wsl_command
    if command == "doctor":
        return wsl_doctor(args)
    if command == "list":
        return wsl_list(args)
    if command == "run":
        return wsl_run(args)
    if command == "path":
        return wsl_path(args)
    raise ValueError(f"Unknown wsl command: {command}")


def wsl_doctor(args: Namespace) -> int:
    path = executable("wsl.exe") or executable("wsl")
    if not path:
        print("wsl not found")
        return 1
    print(f"wsl found: {path}")
    return 0


def wsl_list(args: Namespace) -> int:
    argv = ["wsl", "--list"]
    if args.verbose:
        argv.append("--verbose")
    result = run_command(argv)
    _print_completed(result)
    return result.returncode


def wsl_run(args: Namespace) -> int:
    command = _normalize_command(args.command)
    if not command:
        print("wsl run requires a command")
        return 2
    argv = wsl_run_command(command, distro=args.distro, user=args.user, cwd=args.cwd)
    if args.dry_run:
        print(preview_command(argv).display)
        return 0
    result = run_command(argv)
    _print_completed(result)
    return result.returncode


def wsl_path(args: Namespace) -> int:
    argv = wsl_path_command(args.path, to_windows=args.to_win, distro=args.distro)
    if args.dry_run:
        print(preview_command(argv).display)
        return 0
    result = run_command(argv)
    _print_completed(result)
    return result.returncode


def _print_completed(result) -> None:
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")


def _normalize_command(command: list[str]) -> list[str]:
    if command and command[0] == "--":
        return command[1:]
    return command

from __future__ import annotations

from argparse import Namespace

from ..core.environment import detect_environment, env_local_path, env_markdown, load_env_config, write_env_config
from ..core.paths import ensure_aiflow_dir, project_root


def configure_env_parser(sub) -> None:
    env = sub.add_parser("env", help="Detect and show local aiflow environment configuration")
    env_sub = env.add_subparsers(dest="env_command", required=True)

    detect = env_sub.add_parser("detect", help="Detect paths and tools, then write .aiflow/env.local.toml")
    detect.add_argument("--no-write", action="store_true", help="Print detected environment without writing config")
    detect.set_defaults(func=run_env)

    show = env_sub.add_parser("show", help="Show .aiflow/env.local.toml if it exists")
    show.set_defaults(func=run_env)


def run_env(args: Namespace) -> int:
    if args.env_command == "detect":
        return env_detect(args)
    if args.env_command == "show":
        return env_show(args)
    raise ValueError(f"Unknown env command: {args.env_command}")


def env_detect(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    data = detect_environment(root)
    print(env_markdown(data))
    if not args.no_write:
        path = write_env_config(root, data)
        print(f"written: {path.relative_to(root)}")
    return 0


def env_show(args: Namespace) -> int:
    root = project_root()
    data = load_env_config(root)
    if not data:
        print(f"missing: {env_local_path(root).relative_to(root)}")
        print("Run `aiflow env detect` to create it.")
        return 1
    print(env_markdown(data))
    return 0

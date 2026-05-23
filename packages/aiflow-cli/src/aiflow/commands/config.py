from __future__ import annotations

import json
from argparse import Namespace

from ..core.config import (
    get_config_value,
    load_config,
    parse_config_value,
    save_config,
    set_config_value,
    validate_config,
)
from ..core.paths import ensure_aiflow_dir, project_root


def configure_config_parser(sub) -> None:
    config = sub.add_parser("config", help="Show, edit, and validate .aiflow/config.toml")
    config_sub = config.add_subparsers(dest="config_command", required=True)

    show = config_sub.add_parser("show", help="Show merged project configuration")
    show.add_argument("key", nargs="?", default="", help="Optional dotted key, for example commands.test")
    show.set_defaults(func=run_config)

    set_cmd = config_sub.add_parser("set", help="Set a dotted config key in .aiflow/config.toml")
    set_cmd.add_argument("key", help="Dotted key, for example commands.test")
    set_cmd.add_argument("value", help="Value. TOML arrays and booleans are supported.")
    set_cmd.set_defaults(func=run_config)

    check = config_sub.add_parser("check", help="Validate merged project configuration")
    check.set_defaults(func=run_config)


def run_config(args: Namespace) -> int:
    if args.config_command == "show":
        return config_show(args)
    if args.config_command == "set":
        return config_set(args)
    if args.config_command == "check":
        return config_check(args)
    raise ValueError(f"Unknown config command: {args.config_command}")


def config_show(args: Namespace) -> int:
    root = project_root()
    config = load_config(root)
    if args.key:
        try:
            value = get_config_value(config, args.key)
        except KeyError:
            print(f"Config key not found: {args.key}")
            return 2
        print(json.dumps(value, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(config, indent=2, ensure_ascii=False))
    return 0


def config_set(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    config = load_config(root)
    try:
        set_config_value(config, args.key, parse_config_value(args.value))
    except (KeyError, TypeError) as exc:
        print(f"Config set failed: {exc}")
        return 2
    errors = validate_config(config)
    if errors:
        print("Config validation failed:")
        for error in errors:
            print(f"- {error}")
        return 2
    path = save_config(root, config)
    print(f"written: {path.relative_to(root)}")
    return 0


def config_check(args: Namespace) -> int:
    root = project_root()
    config = load_config(root)
    errors = validate_config(config)
    if errors:
        print("Config validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("config ok")
    return 0

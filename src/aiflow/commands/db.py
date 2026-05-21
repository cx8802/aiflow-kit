from __future__ import annotations

import json
from argparse import Namespace

from ..core.databases import (
    DATABASE_TYPES,
    database_config_path,
    database_local_path,
    list_database_tables,
    load_databases,
    redact_profile,
    resolve_database_profile,
    save_database_file,
    test_database_profile,
)
from ..core.paths import ensure_aiflow_dir, project_root


def configure_db_parser(sub) -> None:
    db = sub.add_parser("db", help="Manage project-level database connection profiles")
    db_sub = db.add_subparsers(dest="db_command", required=True)

    add = db_sub.add_parser("add", help="Add or update a database profile")
    add.add_argument("name")
    add.add_argument("--type", required=True, choices=DATABASE_TYPES)
    add.add_argument("--description", default="")
    add.add_argument("--host", default="")
    add.add_argument("--port", type=int, default=0)
    add.add_argument("--database", default="")
    add.add_argument("--path", default="", help="SQLite database path")
    add.add_argument("--driver", default="", help="Driver name, mainly for SQL Server ODBC")
    add.add_argument("--dsn-env", default="")
    add.add_argument("--user-env", default="")
    add.add_argument("--password-env", default="")
    add.add_argument("--dsn", default="", help="Secret DSN; requires --secret-local")
    add.add_argument("--user", default="", help="Secret user; requires --secret-local")
    add.add_argument("--password", default="", help="Secret password; requires --secret-local")
    add.add_argument("--secret-local", action="store_true", help="Store secrets in .aiflow/databases.local.toml")
    add.add_argument("--force", action="store_true")
    add.set_defaults(func=run_db)

    list_cmd = db_sub.add_parser("list", help="List configured database profiles")
    list_cmd.set_defaults(func=run_db)

    show = db_sub.add_parser("show", help="Show a database profile with secrets redacted")
    show.add_argument("name")
    show.set_defaults(func=run_db)

    test = db_sub.add_parser("test", help="Test a database profile when supported")
    test.add_argument("name")
    test.set_defaults(func=run_db)

    tables = db_sub.add_parser("tables", help="List tables or collections for a database profile")
    tables.add_argument("name")
    tables.add_argument("--schema", default="", help="Optional schema or owner filter")
    tables.set_defaults(func=run_db)


def run_db(args: Namespace) -> int:
    command = args.db_command
    if command == "add":
        return db_add(args)
    if command == "list":
        return db_list(args)
    if command == "show":
        return db_show(args)
    if command == "test":
        return db_test(args)
    if command == "tables":
        return db_tables(args)
    raise ValueError(f"Unknown db command: {command}")


def db_add(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    config, local = load_databases(root)
    profiles = config.setdefault("databases", {})
    local_profiles = local.setdefault("databases", {})

    if args.name in profiles and not args.force:
        print(f"Database profile already exists: {args.name}. Use --force to overwrite.")
        return 2

    secrets = {"dsn": args.dsn, "user": args.user, "password": args.password}
    if any(secrets.values()) and not args.secret_local:
        print("Refusing to store database secrets in tracked config. Use --secret-local or env var names.")
        return 2

    profile = {
        "type": args.type,
        "description": args.description,
        "host": args.host,
        "port": args.port,
        "database": args.database,
        "path": args.path,
        "driver": args.driver,
        "dsn_env": args.dsn_env,
        "user_env": args.user_env,
        "password_env": args.password_env,
    }
    profiles[args.name] = {key: value for key, value in profile.items() if value not in ("", 0, None)}
    save_database_file(database_config_path(root), config)

    if args.secret_local:
        local_profiles[args.name] = {key: value for key, value in secrets.items() if value}
        save_database_file(database_local_path(root), local)

    print(f"written: {database_config_path(root)}")
    if args.secret_local:
        print(f"written: {database_local_path(root)}")
    return 0


def db_list(args: Namespace) -> int:
    root = project_root()
    config, local = load_databases(root)
    profiles = config.get("databases", {})
    if not profiles:
        print("No database profiles configured.")
        return 0
    for name in sorted(profiles):
        profile = profiles[name]
        local_marker = " + local secrets" if name in local.get("databases", {}) else ""
        target = profile.get("database") or profile.get("path") or profile.get("host") or profile.get("dsn_env", "")
        print(f"{name}: {profile.get('type', 'unknown')} {target}{local_marker}")
    return 0


def db_show(args: Namespace) -> int:
    root = project_root()
    config, local = load_databases(root)
    profile = config.get("databases", {}).get(args.name)
    if not profile:
        print(f"Database profile not found: {args.name}")
        return 2
    local_profile = local.get("databases", {}).get(args.name, {})
    print(json.dumps(redact_profile(args.name, profile, local_profile), indent=2, ensure_ascii=False))
    return 0


def db_test(args: Namespace) -> int:
    root = project_root()
    profile = resolve_database_profile(root, args.name)
    if not profile:
        print(f"Database profile not found: {args.name}")
        return 2
    result = test_database_profile(root, profile)
    print(result.message)
    return 0 if result.ok else 1


def db_tables(args: Namespace) -> int:
    root = project_root()
    profile = resolve_database_profile(root, args.name)
    if not profile:
        print(f"Database profile not found: {args.name}")
        return 2
    result = list_database_tables(root, profile, args.schema)
    print(result.message)
    if result.ok and result.rows is not None:
        for row in result.rows:
            print(row)
    return 0 if result.ok else 1

from __future__ import annotations

from argparse import Namespace

from ..core.memory import (
    add_memory_entry,
    has_secret_hint,
    list_memory_entries,
    memory_path,
    search_memory_entries,
    write_compact_context,
)
from ..core.paths import ensure_aiflow_dir, project_root


def configure_memory_parser(sub) -> None:
    memory = sub.add_parser("memory", help="Manage project and explicit global aiflow memory")
    memory_sub = memory.add_subparsers(dest="memory_command", required=True)

    add = memory_sub.add_parser("add", help="Add a memory entry")
    add.add_argument("text", nargs="+", help="Memory text")
    add.add_argument("--global", dest="global_scope", action="store_true", help="Write to user-level aiflow memory")
    add.add_argument("--tag", action="append", default=[], help="Optional tag. Can be used more than once.")
    add.add_argument("--allow-sensitive", action="store_true", help="Allow text that looks sensitive")
    add.set_defaults(func=run_memory)

    list_cmd = memory_sub.add_parser("list", help="List memory entries")
    list_cmd.add_argument("--global", dest="global_scope", action="store_true", help="Read user-level aiflow memory")
    list_cmd.add_argument("--limit", type=int, default=50, help="Maximum entries to show")
    list_cmd.set_defaults(func=run_memory)

    search = memory_sub.add_parser("search", help="Search memory entries")
    search.add_argument("query", nargs="+", help="Search query")
    search.add_argument("--global", dest="global_scope", action="store_true", help="Search user-level aiflow memory")
    search.add_argument("--limit", type=int, default=50, help="Maximum entries to show")
    search.set_defaults(func=run_memory)

    path = memory_sub.add_parser("path", help="Show memory file path")
    path.add_argument("--global", dest="global_scope", action="store_true", help="Show user-level memory path")
    path.set_defaults(func=run_memory)

    compact = sub.add_parser("compact", help="Generate .aiflow/context.compact.md")
    compact.add_argument("--output", default=None, help="Optional output path")
    compact.add_argument("--refresh-context", action="store_true", help="Regenerate .aiflow/context.md before compacting")
    compact.set_defaults(func=run_compact)


def run_memory(args: Namespace) -> int:
    if args.memory_command == "add":
        return memory_add(args)
    if args.memory_command == "list":
        return memory_list(args)
    if args.memory_command == "search":
        return memory_search(args)
    if args.memory_command == "path":
        return memory_show_path(args)
    raise ValueError(f"Unknown memory command: {args.memory_command}")


def memory_add(args: Namespace) -> int:
    root = project_root()
    if not args.global_scope:
        ensure_aiflow_dir(root)
    text = " ".join(args.text)
    if has_secret_hint(text) and not args.allow_sensitive:
        print("Refusing to store text that looks sensitive. Use .aiflow/*.local.toml for secrets.")
        print("Pass --allow-sensitive only for non-secret policy text.")
        return 2
    path = add_memory_entry(root, text, global_scope=args.global_scope, tags=args.tag)
    scope = "global" if args.global_scope else "project"
    print(f"written {scope} memory: {path}")
    return 0


def memory_list(args: Namespace) -> int:
    root = project_root()
    entries = list_memory_entries(root, global_scope=args.global_scope, limit=max(args.limit, 0))
    if not entries:
        print("no memory entries")
        return 0
    for entry in entries:
        print(entry)
    return 0


def memory_search(args: Namespace) -> int:
    root = project_root()
    query = " ".join(args.query)
    entries = search_memory_entries(root, query, global_scope=args.global_scope, limit=max(args.limit, 0))
    if not entries:
        print("no matching memory entries")
        return 0
    for entry in entries:
        print(entry)
    return 0


def memory_show_path(args: Namespace) -> int:
    root = project_root()
    print(memory_path(root, global_scope=args.global_scope))
    return 0


def run_compact(args: Namespace) -> int:
    from pathlib import Path

    root = project_root()
    output = Path(args.output) if args.output else None
    if output and not output.is_absolute():
        output = root / output
    path = write_compact_context(root, output=output, refresh_context=args.refresh_context)
    print(f"written: {path.relative_to(root) if path.is_relative_to(root) else path}")
    return 0

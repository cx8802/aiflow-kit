from __future__ import annotations

from argparse import Namespace

from ..core.graphify import build_graphify, graphify_dir
from ..core.paths import ensure_aiflow_dir, project_root


def configure_graphify_parser(sub) -> None:
    graphify = sub.add_parser("graphify", help="Generate the Graphify project knowledge layer")
    graphify_sub = graphify.add_subparsers(dest="graphify_command", required=True)

    build = graphify_sub.add_parser("build", help="Build .aiflow/graphify from docs and project memory")
    build.set_defaults(func=run_graphify)


def run_graphify(args: Namespace) -> int:
    if args.graphify_command == "build":
        root = project_root()
        ensure_aiflow_dir(root)
        result = build_graphify(root)
        output = graphify_dir(root)
        print(f"written: {output.relative_to(root)}")
        print(f"sources: {len(result['knowledge']['sources'])}")
        print(f"concepts: {len(result['concepts']['concepts'])}")
        return 0
    raise ValueError(f"Unknown graphify command: {args.graphify_command}")

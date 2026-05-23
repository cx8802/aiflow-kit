from __future__ import annotations

from argparse import Namespace

from ..core.codegraph import build_codegraph, codegraph_dir
from ..core.paths import ensure_aiflow_dir, project_root


def configure_codegraph_parser(sub) -> None:
    codegraph = sub.add_parser("codegraph", help="Generate the CodeGraph code structure layer")
    codegraph_sub = codegraph.add_subparsers(dest="codegraph_command", required=True)

    scan = codegraph_sub.add_parser("scan", help="Scan source files into .aiflow/codegraph")
    scan.set_defaults(func=run_codegraph)


def run_codegraph(args: Namespace) -> int:
    if args.codegraph_command == "scan":
        root = project_root()
        ensure_aiflow_dir(root)
        result = build_codegraph(root)
        output = codegraph_dir(root)
        print(f"written: {output.relative_to(root)}")
        print(f"modules: {len(result['modules']['modules'])}")
        print(f"symbols: {len(result['symbols']['symbols'])}")
        return 0
    raise ValueError(f"Unknown codegraph command: {args.codegraph_command}")

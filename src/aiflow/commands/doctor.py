from __future__ import annotations

import shutil
from argparse import Namespace

from ..core.config import config_path, load_config
from ..core.files import write_text_safely
from ..core.markdown import now_stamp
from ..core.paths import ensure_aiflow_dir, project_root


TOOLS = ["git", "rg", "python", "go", "node", "npm.cmd", "java", "mvn"]


def run_doctor(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    config = load_config(root)

    rows = []
    ok = True
    for tool in TOOLS:
        found = shutil.which(tool)
        rows.append((tool, "ok" if found else "missing", found or ""))
        if tool in {"git", "python"} and not found:
            ok = False

    config_exists = config_path(root).exists()
    env_bat_exists = (root / "scripts" / "use-project-env.bat").exists()

    lines = [
        "# Doctor",
        "",
        f"Generated at: {now_stamp()}",
        "",
        "## Tools",
        "",
        "| Tool | Status | Path |",
        "| --- | --- | --- |",
    ]
    lines.extend(f"| `{tool}` | {status} | `{path}` |" for tool, status, path in rows)
    lines.extend(
        [
            "",
            "## Project Files",
            "",
            f"- Config: {'ok' if config_exists else 'missing'} `{config_path(root)}`",
            f"- BAT environment script: {'ok' if env_bat_exists else 'missing'} `scripts/use-project-env.bat`",
            "",
            "## Commands",
            "",
        ]
    )
    commands = config.get("commands", {})
    if any(commands.values()):
        lines.extend(f"- {name}: `{command}`" for name, command in commands.items() if command)
    else:
        lines.append("- No verification commands configured.")

    report = "\n".join(lines) + "\n"
    if not args.no_write:
        write_text_safely(root / ".aiflow" / "doctor.md", report, force=True)
    print(report)
    return 0 if ok else 1

from __future__ import annotations

from argparse import Namespace

from ..core.config import config_path, load_config
from ..core.environment import detect_environment, env_local_path
from ..core.files import write_text_safely
from ..core.markdown import now_stamp
from ..core.paths import ensure_aiflow_dir, project_root


def run_doctor(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    config = load_config(root)
    env_data = detect_environment(root)

    rows = []
    ok = True
    for tool, info in env_data.get("tools", {}).items():
        found = info.get("path", "")
        rows.append((tool, info.get("status", "missing"), found, info.get("version", "")))
        if tool in {"git", "python"} and not found:
            ok = False

    config_exists = config_path(root).exists()
    env_exists = env_local_path(root).exists()
    env_bat_exists = (root / "scripts" / "use-project-env.bat").exists()

    lines = [
        "# Doctor",
        "",
        f"Generated at: {now_stamp()}",
        "",
        "## Tools",
        "",
        "| Tool | Status | Path | Version |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(f"| `{tool}` | {status} | `{path}` | `{version}` |" for tool, status, path, version in rows)
    lines.extend(
        [
            "",
            "## Project Files",
            "",
            f"- Config: {'ok' if config_exists else 'missing'} `{config_path(root)}`",
            f"- Local env config: {'ok' if env_exists else 'missing'} `{env_local_path(root)}`",
            f"- BAT environment script: {'ok' if env_bat_exists else 'missing'} `scripts/use-project-env.bat`",
            "",
            "## Detected Paths",
            "",
            f"- Project root: `{env_data['paths']['project_root']}`",
            f"- aiflow-kit root: `{env_data['paths']['aiflow_kit_root']}`",
            f"- aiflow wrapper: `{env_data['paths']['aiflow_dev_bat']}`",
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

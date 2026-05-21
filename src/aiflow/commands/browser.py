from __future__ import annotations

import zipfile
from argparse import Namespace
from pathlib import Path

from ..core.browser import (
    BrowserBridgeServer,
    actions_dir,
    browser_config,
    capture_dir,
    display_path,
    elements_dir,
    ensure_browser_token,
    read_browser_token,
    token_path,
    write_automation_job,
    write_capture,
)
from ..core.paths import ensure_aiflow_dir, project_root
from ..core.resources import browser_extension_root


LOOPBACK_HOSTS = {"127.0.0.1", "localhost"}
EXTENSION_PACKAGE_EXCLUDES = {"README.md", "package.json", "package-lock.json"}


def configure_browser_parser(sub) -> None:
    browser = sub.add_parser("browser", help="Capture browser context into the current aiflow project")
    browser_sub = browser.add_subparsers(dest="browser_command", required=True)

    extension_dir = browser_sub.add_parser("extension-dir", help="Show bundled Chrome/Edge extension directory")
    extension_dir.set_defaults(func=run_browser)

    doctor = browser_sub.add_parser("doctor", help="Check browser companion configuration")
    doctor.set_defaults(func=run_browser)

    capture = browser_sub.add_parser("capture", help="Write a browser capture without starting the bridge")
    capture.add_argument("--type", default="selection", choices=["page", "selection"], help="Capture type")
    capture.add_argument("--url", default="", help="Source URL")
    capture.add_argument("--title", default="", help="Page title")
    capture.add_argument("--selection", default="", help="Selected page text")
    capture.add_argument("--note", default="", help="User note")
    capture.set_defaults(func=run_browser)

    serve = browser_sub.add_parser("serve", help="Run the localhost browser capture bridge")
    serve.add_argument("--host", default=None, help="Loopback host override")
    serve.add_argument("--port", type=int, default=None, help="Port override")
    serve.set_defaults(func=run_browser)

    pack = browser_sub.add_parser("pack", help="Build a Chrome/Edge extension zip package")
    pack.add_argument("--output", type=Path, default=None, help="Zip output path")
    pack.add_argument("--force", action="store_true", help="Overwrite an existing zip package")
    pack.set_defaults(func=run_browser)

    automate = browser_sub.add_parser("automate", help="Queue a browser automation job for the extension")
    automate.add_argument(
        "--step",
        action="append",
        required=True,
        help="Step as action;;selector;;value. Supported actions: extract, click, fill, wait.",
    )
    automate.add_argument("--note", default="", help="Optional job note")
    automate.set_defaults(func=run_browser)


def run_browser(args: Namespace) -> int:
    command = args.browser_command
    if command == "extension-dir":
        return browser_extension_dir(args)
    if command == "doctor":
        return browser_doctor(args)
    if command == "capture":
        return browser_capture(args)
    if command == "serve":
        return browser_serve(args)
    if command == "pack":
        return browser_pack(args)
    if command == "automate":
        return browser_automate(args)
    raise ValueError(f"Unknown browser command: {command}")


def browser_extension_dir(args: Namespace) -> int:
    print(browser_extension_root())
    return 0


def browser_doctor(args: Namespace) -> int:
    root = project_root()
    config = browser_config(root)
    extension_root = Path(str(browser_extension_root()))
    token = read_browser_token(root, config)
    rows = [
        ("enabled", "ok" if config.get("enabled") else "disabled", str(config.get("enabled", False))),
        ("bridge", "ok", f"{config.get('host')}:{config.get('port')}"),
        ("extension", "ok" if extension_root.exists() else "missing", str(extension_root)),
        ("capture dir", "ok", display_path(root, capture_dir(root, config))),
        ("elements dir", "ok", display_path(root, elements_dir(root, config))),
        ("actions dir", "ok", display_path(root, actions_dir(root, config))),
        ("token", "ok" if token else "missing", display_path(root, token_path(root, config))),
    ]
    print("# Browser Companion Doctor")
    print("")
    print("| Check | Status | Detail |")
    print("| --- | --- | --- |")
    for name, status, detail in rows:
        print(f"| {name} | {status} | `{detail}` |")
    return 0


def browser_capture(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    path = write_capture(
        root,
        {
            "type": args.type,
            "url": args.url,
            "title": args.title,
            "selection": args.selection,
            "note": args.note,
        },
    )
    print(f"written: {display_path(root, path)}")
    return 0


def browser_serve(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    config = browser_config(root)
    host = args.host or str(config.get("host", "127.0.0.1"))
    port = args.port if args.port is not None else int(config.get("port", 8765))
    if host not in LOOPBACK_HOSTS:
        print("Refusing unsupported browser bridge host. Use 127.0.0.1 or localhost.")
        return 2

    token = ensure_browser_token(root, config)
    server = BrowserBridgeServer(root, host, port, config, token)
    print(f"browser bridge: http://{host}:{server.server_port}")
    print(f"capture dir: {display_path(root, capture_dir(root, config))}")
    print(f"elements dir: {display_path(root, elements_dir(root, config))}")
    print(f"extension dir: {browser_extension_root()}")
    print(f"project token: {token}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("browser bridge stopped")
    finally:
        server.server_close()
    return 0


def browser_pack(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    extension_root = Path(str(browser_extension_root()))
    output = args.output or (root / ".aiflow" / "dist" / "aiflow-browser-extension.zip")
    if not output.is_absolute():
        output = root / output
    if output.exists() and not args.force:
        print(f"Refusing to overwrite existing browser package: {display_path(root, output)}")
        print("Rerun with --force to replace it.")
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for file in extension_package_files(extension_root):
            package.write(file, file.relative_to(extension_root).as_posix())
    print(f"written: {display_path(root, output)}")
    return 0


def browser_automate(args: Namespace) -> int:
    root = project_root()
    ensure_aiflow_dir(root)
    try:
        path = write_automation_job(root, [parse_step(step) for step in args.step], note=args.note)
    except ValueError as exc:
        print(f"Automation job failed: {exc}")
        return 2
    print(f"queued: {display_path(root, path)}")
    return 0


def parse_step(value: str) -> dict[str, str]:
    delimiter = ";;" if ";;" in value else "|"
    parts = value.split(delimiter, 2)
    action = parts[0].strip()
    selector = parts[1].strip() if len(parts) > 1 else ""
    step_value = parts[2] if len(parts) > 2 else ""
    return {"action": action, "selector": selector, "value": step_value}


def extension_package_files(extension_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(item for item in extension_root.rglob("*") if item.is_file()):
        rel = path.relative_to(extension_root)
        parts = set(rel.parts)
        if "node_modules" in parts or "dist" in parts:
            continue
        if rel.as_posix() in EXTENSION_PACKAGE_EXCLUDES:
            continue
        files.append(path)
    return files

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aiflow.core.browser import BrowserBridgeServer, browser_config
from aiflow.core.claude_agent import command_env


def run_aiflow(cwd: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command_env = os.environ.copy()
    command_env["PYTHONPATH"] = str(SRC)
    if env:
        command_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "aiflow", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        env=command_env,
    )


class CliSmokeTests(unittest.TestCase):
    def test_init_generates_project_files_without_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "init", "--no-context")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((cwd / "AGENTS.md").exists())
            self.assertTrue((cwd / "CLAUDE.md").exists())
            self.assertTrue((cwd / ".aiflow" / "config.toml").exists())
            self.assertFalse((cwd / ".aiflow" / "context.md").exists())

    def test_init_keeps_claude_agent_runtime_paths_out_of_project_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "init", "--no-context")
            self.assertEqual(result.returncode, 0, result.stderr)
            config = (cwd / ".aiflow" / "config.toml").read_text(encoding="utf-8")
            self.assertNotIn("package_dir =", config)
            self.assertNotIn("runner =", config)

    def test_context_uses_file_scan_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "README.md").write_text("# Demo\n", encoding="utf-8")
            result = run_aiflow(cwd, "context")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = (cwd / ".aiflow" / "context.md").read_text(encoding="utf-8")
            self.assertIn("## File Scan", report)
            self.assertIn("README.md", report)

    def test_context_compact_generates_compact_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "README.md").write_text("# Demo\n", encoding="utf-8")
            memory = run_aiflow(cwd, "memory", "add", "Use project-level memory for repository facts")
            self.assertEqual(memory.returncode, 0, memory.stderr)

            result = run_aiflow(cwd, "context", "--compact")
            self.assertEqual(result.returncode, 0, result.stderr)
            compact = (cwd / ".aiflow" / "context.compact.md").read_text(encoding="utf-8")
            self.assertIn("# Compact Context", compact)
            self.assertIn("## Project Memory", compact)
            self.assertIn("Use project-level memory", compact)

    def test_memory_add_list_search_and_sensitive_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            add = run_aiflow(cwd, "memory", "add", "Backend uses FastAPI", "--tag", "architecture")
            self.assertEqual(add.returncode, 0, add.stderr)
            self.assertTrue((cwd / ".aiflow" / "memory.md").exists())

            listing = run_aiflow(cwd, "memory", "list")
            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertIn("Backend uses FastAPI", listing.stdout)
            self.assertIn("#architecture", listing.stdout)

            search = run_aiflow(cwd, "memory", "search", "fastapi")
            self.assertEqual(search.returncode, 0, search.stderr)
            self.assertIn("Backend uses FastAPI", search.stdout)

            sensitive = run_aiflow(cwd, "memory", "add", "password=123456")
            self.assertEqual(sensitive.returncode, 2)
            self.assertIn("Refusing to store text", sensitive.stdout)

    def test_memory_global_scope_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            fake_home = cwd / "home"
            fake_home.mkdir()
            add = run_aiflow(
                cwd,
                "memory",
                "add",
                "Prefer BAT scripts on Windows",
                "--global",
                env={"USERPROFILE": str(fake_home)},
            )
            self.assertEqual(add.returncode, 0, add.stderr)
            self.assertTrue((fake_home / ".aiflow" / "memory.md").exists())
            self.assertFalse((cwd / ".aiflow" / "memory.md").exists())

    def test_review_handles_utf8_paths_on_windows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            init = subprocess.run(["git", "init"], cwd=cwd, text=True, capture_output=True)
            if init.returncode != 0:
                self.skipTest("git is not available")
            (cwd / "数据库.md").write_text("# demo\n", encoding="utf-8")

            result = run_aiflow(cwd, "review")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((cwd / ".aiflow" / "review.md").exists())

    def test_install_skills_defaults_to_project_codex_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "install-skills")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((cwd / ".agents" / "skills" / "project-analysis" / "SKILL.md").exists())
            self.assertTrue((cwd / ".agents" / "skills" / "code-review-release" / "SKILL.md").exists())
            self.assertTrue((cwd / ".agents" / "skills" / "multi-agent-orchestrator" / "SKILL.md").exists())
            self.assertTrue((cwd / ".agents" / "skills" / "frontend-design" / "SKILL.md").exists())
            self.assertTrue((cwd / ".agents" / "skills" / "playwright-verify" / "SKILL.md").exists())
            guide = (cwd / ".agents" / "skills" / "aiflow-kit-guide" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(str(ROOT), guide)
            self.assertNotIn("{{ AIFLOW_KIT_ROOT }}", guide)

    def test_env_detect_writes_local_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "env", "detect")
            self.assertEqual(result.returncode, 0, result.stderr)
            env_file = cwd / ".aiflow" / "env.local.toml"
            self.assertTrue(env_file.exists())
            content = env_file.read_text(encoding="utf-8")
            self.assertIn("aiflow_kit_root", content)
            self.assertIn(str(ROOT).replace("\\", "\\\\"), content)
            self.assertIn("[tools.python]", content)

            show = run_aiflow(cwd, "env", "show")
            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertIn("## Tools", show.stdout)

    def test_frontend_install_dry_run_prints_aiflow_kit_playwright_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            kit_root = cwd / "kit-root"
            result = run_aiflow(
                cwd,
                "frontend",
                "install",
                "--dry-run",
                env={"AIFLOW_KIT_ROOT": str(kit_root)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("@playwright/test", result.stdout)
            self.assertIn(str(kit_root / ".tools" / "frontend-tools"), result.stdout)
            self.assertIn(str(kit_root / ".tools" / "ms-playwright"), result.stdout)
            self.assertIn("playwright", result.stdout)
            self.assertIn("would ensure aiflow-kit .gitignore entries", result.stdout)

    def test_frontend_install_skip_browsers_uses_aiflow_kit_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            kit_root = cwd / "kit-root"
            fake_bin = cwd / "fake-bin"
            fake_bin.mkdir()
            fake_npm = fake_bin / ("npm.cmd" if os.name == "nt" else "npm")
            if os.name == "nt":
                fake_npm.write_text("@echo off\necho fake npm %*\nexit /b 0\n", encoding="utf-8")
            else:
                fake_npm.write_text("#!/bin/sh\necho fake npm \"$@\"\n", encoding="utf-8")
                fake_npm.chmod(0o755)

            env = {
                "AIFLOW_KIT_ROOT": str(kit_root),
                "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
            }
            result = run_aiflow(cwd, "frontend", "install", "--skip-browsers", env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((kit_root / ".tools" / "frontend-tools").exists())
            self.assertTrue((kit_root / ".tools" / "ms-playwright").exists())
            self.assertFalse((cwd / ".tools").exists())
            self.assertFalse((cwd / ".gitignore").exists())
            gitignore = (kit_root / ".gitignore").read_text(encoding="utf-8")
            self.assertIn(".tools/", gitignore)
            self.assertIn(".cache/", gitignore)

    def test_browser_extension_dir_points_to_bundled_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "browser", "extension-dir")
            self.assertEqual(result.returncode, 0, result.stderr)
            extension_dir = Path(result.stdout.strip())
            self.assertTrue((extension_dir / "manifest.json").exists())
            self.assertTrue((extension_dir / "adapters" / "index.json").exists())

    def test_browser_pack_writes_extension_zip_with_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "browser", "pack")
            self.assertEqual(result.returncode, 0, result.stderr)
            package = cwd / ".aiflow" / "dist" / "aiflow-browser-extension.zip"
            self.assertTrue(package.exists())
            with zipfile.ZipFile(package) as archive:
                names = set(archive.namelist())
            self.assertIn("manifest.json", names)
            self.assertIn("settings.html", names)
            self.assertIn("devtools.html", names)
            self.assertIn("devtools-panel.html", names)
            self.assertIn("adapters/index.json", names)
            self.assertIn("adapters/generic-page.json", names)
            self.assertNotIn("sidepanel.html", names)

    def test_browser_capture_writes_project_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(
                cwd,
                "browser",
                "capture",
                "--url",
                "https://example.test/docs",
                "--title",
                "Docs",
                "--selection",
                "selected text",
                "--note",
                "implementation context",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            captures = sorted((cwd / ".aiflow" / "browser" / "captures").glob("*.md"))
            self.assertEqual(len(captures), 1)
            content = captures[0].read_text(encoding="utf-8")
            self.assertIn("# Browser Capture", content)
            self.assertIn("https://example.test/docs", content)
            self.assertIn("selected text", content)
            self.assertIn("implementation context", content)

    def test_browser_automate_queues_pending_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(
                cwd,
                "browser",
                "automate",
                "--step",
                "open;;https://example.test/search",
                "--step",
                "snapshot",
                "--step",
                "fill;;#search;;aiflow",
                "--step",
                "click;;button[type=submit]",
                "--step",
                "scroll;;;;down",
                "--step",
                "wait;;;;1000",
                "--step",
                "extract;;main",
                "--note",
                "search docs",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            jobs = sorted((cwd / ".aiflow" / "browser" / "actions" / "pending").glob("*.json"))
            self.assertEqual(len(jobs), 1)
            payload = json.loads(jobs[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["note"], "search docs")
            self.assertEqual([step["action"] for step in payload["steps"]], ["open", "snapshot", "fill", "click", "scroll", "wait", "extract"])
            self.assertEqual(payload["steps"][0]["value"], "https://example.test/search")
            self.assertEqual(payload["steps"][4]["value"], "down")
            self.assertEqual(payload["steps"][5]["value"], "1000")

    def test_browser_bridge_requires_token_and_writes_capture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            config = browser_config(cwd)
            server = BrowserBridgeServer(cwd, "127.0.0.1", 0, config, "test-token")
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            url = f"http://127.0.0.1:{server.server_port}/captures"
            body = json.dumps(
                {
                    "type": "selection",
                    "url": "https://example.test/source",
                    "title": "Source",
                    "selection": "bridge selection",
                    "note": "bridge note",
                }
            ).encode("utf-8")
            try:
                unauthorized = urllib.request.Request(
                    url,
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(unauthorized, timeout=5)
                self.assertEqual(error.exception.code, 401)

                authorized = urllib.request.Request(
                    url,
                    data=body,
                    headers={"Content-Type": "application/json", "X-Aiflow-Token": "test-token"},
                    method="POST",
                )
                with urllib.request.urlopen(authorized, timeout=5) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self.assertIn(".aiflow", payload["capture"])
                captures = sorted((cwd / ".aiflow" / "browser" / "captures").glob("*.md"))
                self.assertEqual(len(captures), 1)
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=5)

    def test_browser_bridge_writes_selected_element(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            config = browser_config(cwd)
            server = BrowserBridgeServer(cwd, "127.0.0.1", 0, config, "test-token")
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            url = f"http://127.0.0.1:{server.server_port}/elements"
            body = json.dumps(
                {
                    "url": "https://example.test/source",
                    "title": "Source",
                    "selector": "main > button:nth-of-type(1)",
                    "tagName": "button",
                    "id": "submit",
                    "className": "primary",
                    "text": "Submit",
                    "attributes": {"type": "button", "data-testid": "submit"},
                    "rect": {"x": 10, "y": 20, "width": 100, "height": 30},
                }
            ).encode("utf-8")
            try:
                unauthorized = urllib.request.Request(
                    url,
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(unauthorized, timeout=5)
                self.assertEqual(error.exception.code, 401)

                authorized = urllib.request.Request(
                    url,
                    data=body,
                    headers={"Content-Type": "application/json", "X-Aiflow-Token": "test-token"},
                    method="POST",
                )
                with urllib.request.urlopen(authorized, timeout=5) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self.assertIn(".aiflow", payload["element"])
                elements = sorted((cwd / ".aiflow" / "browser" / "elements").glob("*.json"))
                self.assertEqual(len(elements), 1)
                element = json.loads(elements[0].read_text(encoding="utf-8"))
                self.assertEqual(element["selector"], "main > button:nth-of-type(1)")
                self.assertEqual(element["text"], "Submit")
                self.assertEqual(element["attributes"]["data-testid"], "submit")
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=5)

    def test_browser_bridge_writes_page_and_request_captures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            config = browser_config(cwd)
            server = BrowserBridgeServer(cwd, "127.0.0.1", 0, config, "test-token")
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                page_request = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_port}/pages",
                    data=json.dumps(
                        {
                            "url": "https://example.test/app?access_token=secret&view=list",
                            "title": "App",
                            "html": "<html><body>App</body></html>",
                            "text": "App",
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json", "X-Aiflow-Token": "test-token"},
                    method="POST",
                )
                with urllib.request.urlopen(page_request, timeout=5) as response:
                    page_payload = json.loads(response.read().decode("utf-8"))
                self.assertIn(".aiflow", page_payload["page"])

                requests_request = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_port}/requests",
                    data=json.dumps(
                        {
                            "url": "https://example.test/app",
                            "title": "App",
                            "entries": [
                                {
                                    "url": "https://api.example.test/items?token=secret&id=1",
                                    "method": "GET",
                                    "status": 200,
                                    "statusText": "OK",
                                    "mimeType": "application/json",
                                    "resourceType": "xhr",
                                    "time": 42.5,
                                }
                            ],
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json", "X-Aiflow-Token": "test-token"},
                    method="POST",
                )
                with urllib.request.urlopen(requests_request, timeout=5) as response:
                    requests_payload = json.loads(response.read().decode("utf-8"))
                self.assertIn(".aiflow", requests_payload["requests"])

                pages = sorted((cwd / ".aiflow" / "browser" / "pages").glob("*.json"))
                requests = sorted((cwd / ".aiflow" / "browser" / "requests").glob("*.json"))
                self.assertEqual(len(pages), 1)
                self.assertEqual(len(requests), 1)
                page = json.loads(pages[0].read_text(encoding="utf-8"))
                request_capture = json.loads(requests[0].read_text(encoding="utf-8"))
                self.assertIn("access_token=%5BREDACTED%5D", page["url"])
                self.assertIn("token=%5BREDACTED%5D", request_capture["entries"][0]["url"])
                self.assertNotIn("headers", request_capture["entries"][0])
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=5)

    def test_browser_bridge_serves_and_completes_automation_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            enqueue = run_aiflow(cwd, "browser", "automate", "--step", "extract;;main")
            self.assertEqual(enqueue.returncode, 0, enqueue.stderr)
            config = browser_config(cwd)
            server = BrowserBridgeServer(cwd, "127.0.0.1", 0, config, "test-token")
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                next_request = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_port}/automation/next",
                    headers={"X-Aiflow-Token": "test-token"},
                    method="GET",
                )
                with urllib.request.urlopen(next_request, timeout=5) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self.assertIsNotNone(payload["job"])
                job_id = payload["job"]["id"]

                result_request = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_port}/automation/{job_id}/result",
                    data=json.dumps({"status": "completed", "results": [{"text": "done"}]}).encode("utf-8"),
                    headers={"Content-Type": "application/json", "X-Aiflow-Token": "test-token"},
                    method="POST",
                )
                with urllib.request.urlopen(result_request, timeout=5) as response:
                    result_payload = json.loads(response.read().decode("utf-8"))
                self.assertIn("completed", result_payload["result"])
                self.assertFalse((cwd / ".aiflow" / "browser" / "actions" / "pending" / f"{job_id}.json").exists())
                self.assertTrue((cwd / ".aiflow" / "browser" / "actions" / "completed" / f"{job_id}.json").exists())
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=5)

    def test_claude_agent_install_dry_run_uses_aiflow_kit_sdk_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "claude-agent", "install", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(ROOT / ".tools" / "claude-agent"), result.stdout)
            self.assertIn("@anthropic-ai/claude-agent-sdk", result.stdout)

    def test_claude_agent_run_dry_run_builds_read_only_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / ".aiflow").mkdir()
            (cwd / ".aiflow" / "context.compact.md").write_text("# Compact\n", encoding="utf-8")
            result = run_aiflow(cwd, "claude-agent", "run", "summarize", "commands", "--model", "test-model", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('"model": "test-model"', result.stdout)
            self.assertIn('"claudeCodeExecutable"', result.stdout)
            self.assertIn('"allowedTools"', result.stdout)
            self.assertIn('"Read"', result.stdout)
            self.assertIn('"disallowedTools"', result.stdout)
            self.assertIn('"Bash"', result.stdout)
            self.assertIn(".aiflow/context.compact.md", result.stdout)

    def test_claude_agent_run_dry_run_includes_task_edit_scope_and_verify_after(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            task_dir = cwd / ".aiflow" / "agents" / "tasks"
            task_dir.mkdir(parents=True)
            (task_dir / "001-demo.md").write_text("# 001-demo\n\n## Objective\n\nUpdate docs.\n", encoding="utf-8")

            result = run_aiflow(
                cwd,
                "claude-agent",
                "run",
                "update",
                "docs",
                "--model",
                "test-model",
                "--dry-run",
                "--allow-edit",
                "--edit-scope",
                "docs",
                "--task-id",
                "001-demo",
                "--verify-after",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["taskId"], "001-demo")
            self.assertEqual(payload["editScope"], ["docs"])
            self.assertEqual(payload["postRunVerifyCommand"], "aiflow verify --auto --continue-on-error")
            self.assertIn("Aiflow Task Binding", payload["prompt"])
            self.assertIn("Do not edit files outside", payload["prompt"])

    def test_claude_agent_edit_scope_requires_allow_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_aiflow(
                Path(tmp),
                "claude-agent",
                "run",
                "update",
                "--model",
                "test-model",
                "--dry-run",
                "--edit-scope",
                "src",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("--edit-scope requires --allow-edit", result.stdout)

    def test_claude_agent_run_requires_configured_alias_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "claude-agent", "run", "summarize", "--dry-run")
            self.assertEqual(result.returncode, 2)
            self.assertIn("claude_agent.small_model is empty", result.stdout)

    def test_claude_agent_runner_passes_budget_to_sdk(self) -> None:
        node = shutil.which("node.exe" if os.name == "nt" else "node") or shutil.which("node")
        if not node:
            self.skipTest("node is not available")

        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            package_dir = cwd / "package"
            sdk_dir = package_dir / "node_modules" / "@anthropic-ai" / "claude-agent-sdk"
            sdk_dir.mkdir(parents=True)
            (package_dir / "package.json").write_text('{"private":true}\n', encoding="utf-8")
            (sdk_dir / "package.json").write_text(
                '{"name":"@anthropic-ai/claude-agent-sdk","type":"module","exports":"./index.mjs"}\n',
                encoding="utf-8",
            )
            (sdk_dir / "index.mjs").write_text(
                """
export async function* query({ options }) {
  yield {
    type: "result",
    result: String(options.maxBudgetUsd),
    total_cost_usd: 0,
    usage: {}
  };
}
""".strip()
                + "\n",
                encoding="utf-8",
            )
            output_dir = cwd / "output"
            input_file = cwd / "input.json"
            input_file.write_text(
                """
{
  "cwd": ".",
  "task": "run",
  "prompt": "budget probe",
  "model": "test-model",
  "packageDir": "PACKAGE_DIR",
  "outputDir": "OUTPUT_DIR",
  "contextFiles": [],
  "allowedTools": ["Read"],
  "disallowedTools": ["Write"],
  "permissionMode": "dontAsk",
  "maxTurns": 1,
  "maxBudgetUsd": 0.2
}
""".strip()
                .replace("PACKAGE_DIR", str(package_dir).replace("\\", "\\\\"))
                .replace("OUTPUT_DIR", str(output_dir).replace("\\", "\\\\"))
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [node, str(ROOT / "node" / "claude-agent-runner" / "runner.mjs"), str(input_file)],
                cwd=cwd,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((output_dir / "result.md").read_text(encoding="utf-8"), "0.2\n")

    def test_claude_agent_local_env_maps_auth_token_and_base_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            local = cwd / ".aiflow" / "claude-agent.local.toml"
            local.parent.mkdir()
            local.write_text(
                """
[env]
MINIMAX_AUTH = "local-token"
MINIMAX_BASE_URL = "https://example.invalid/anthropic"
""".strip()
                + "\n",
                encoding="utf-8",
            )

            env = command_env(
                cwd,
                {
                    "api_key_env": "MINIMAX_AUTH",
                    "auth_token_env": "MINIMAX_AUTH",
                    "base_url_env": "MINIMAX_BASE_URL",
                },
                use_proxy=False,
            )

            self.assertEqual(env["ANTHROPIC_API_KEY"], "local-token")
            self.assertEqual(env["ANTHROPIC_AUTH_TOKEN"], "local-token")
            self.assertEqual(env["ANTHROPIC_BASE_URL"], "https://example.invalid/anthropic")

    def test_claude_agent_usage_reads_usage_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            usage_dir = cwd / ".aiflow" / "claude-agent"
            usage_dir.mkdir(parents=True)
            (usage_dir / "usage.jsonl").write_text(
                '{"task":"run","model":"test-model","total_cost_usd":0.01}\n',
                encoding="utf-8",
            )
            result = run_aiflow(cwd, "claude-agent", "usage")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("test-model", result.stdout)
            self.assertIn("total_cost_usd", result.stdout)

    def test_agents_init_plan_status_and_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            init = run_aiflow(cwd, "agents", "init")
            self.assertEqual(init.returncode, 0, init.stderr)
            self.assertTrue((cwd / ".aiflow" / "agents" / "roles.toml").exists())
            self.assertTrue((cwd / ".aiflow" / "agents" / "status.md").exists())
            self.assertTrue((cwd / ".aiflow" / "agents" / "handoff.md").exists())

            plan = run_aiflow(cwd, "agents", "plan", "add", "multi", "agent", "workflow")
            self.assertEqual(plan.returncode, 0, plan.stderr)
            task_files = sorted((cwd / ".aiflow" / "agents" / "tasks").glob("*.md"))
            self.assertEqual(len(task_files), 4)
            self.assertTrue(any("001-explore" in path.name for path in task_files))

            status = run_aiflow(cwd, "agents", "status")
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertIn("tasks: 4", status.stdout)

            handoff = run_aiflow(cwd, "agents", "handoff", "demo", "--force")
            self.assertEqual(handoff.returncode, 0, handoff.stderr)
            self.assertIn("written:", handoff.stdout)

            start = run_aiflow(cwd, "agents", "start", "001-explore", "reading files")
            self.assertEqual(start.returncode, 0, start.stderr)
            status_text = (cwd / ".aiflow" / "agents" / "status.md").read_text(encoding="utf-8")
            self.assertIn("in_progress", status_text)

            done = run_aiflow(cwd, "agents", "done", "001-explore")
            self.assertEqual(done.returncode, 0, done.stderr)
            status_text = (cwd / ".aiflow" / "agents" / "status.md").read_text(encoding="utf-8")
            self.assertIn("done", status_text)

            block = run_aiflow(cwd, "agents", "block", "002-implement", "waiting for scope")
            self.assertEqual(block.returncode, 0, block.stderr)
            status_text = (cwd / ".aiflow" / "agents" / "status.md").read_text(encoding="utf-8")
            self.assertIn("blocked", status_text)

    def test_config_show_set_and_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            init = run_aiflow(cwd, "init", "--no-context")
            self.assertEqual(init.returncode, 0, init.stderr)

            set_cmd = run_aiflow(cwd, "config", "set", "commands.test", "python --version")
            self.assertEqual(set_cmd.returncode, 0, set_cmd.stderr)

            show = run_aiflow(cwd, "config", "show", "commands.test")
            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertIn("python --version", show.stdout)

            check = run_aiflow(cwd, "config", "check")
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertIn("config ok", check.stdout)

    def test_verify_dry_run_uses_configured_commands_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / ".aiflow").mkdir()
            (cwd / ".aiflow" / "config.toml").write_text(
                """
[commands]
lint = "python --version"
test = "python --version"
""".strip()
                + "\n",
                encoding="utf-8",
            )
            result = run_aiflow(cwd, "verify", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = (cwd / ".aiflow" / "verify.md").read_text(encoding="utf-8")
            self.assertIn("lint: `python --version`", report)
            self.assertIn("test: `python --version`", report)
            self.assertIn("dry-run", report)

    def test_verify_auto_detects_unittest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "tests").mkdir()
            (cwd / "tests" / "test_demo.py").write_text("import unittest\n", encoding="utf-8")
            result = run_aiflow(cwd, "verify", "--auto", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = (cwd / ".aiflow" / "verify.md").read_text(encoding="utf-8")
            self.assertIn("python -m unittest discover -s tests", report)

    def test_verify_auto_detects_node_scripts_and_compileall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "src").mkdir()
            (cwd / "src" / "demo.py").write_text("value = 1\n", encoding="utf-8")
            (cwd / "package.json").write_text(
                json.dumps(
                    {
                        "scripts": {
                            "lint": "eslint .",
                            "typecheck": "tsc --noEmit",
                            "check": "node --check index.js",
                            "build": "vite build",
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = run_aiflow(cwd, "verify", "--auto", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = (cwd / ".aiflow" / "verify.md").read_text(encoding="utf-8")
            node_runner = "npm.cmd" if os.name == "nt" else "npm"
            self.assertIn(f"lint: `{node_runner} run lint`", report)
            self.assertIn(f"typecheck: `{node_runner} run typecheck`", report)
            self.assertIn(f"test: `{node_runner} run check`", report)
            self.assertIn(f"build: `python -m compileall src && {node_runner} run build`", report)

    def test_codex_user_install_requires_explicit_global_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            fake_home = cwd / "home"
            fake_home.mkdir()
            result = run_aiflow(cwd, "install-skills", "--target", "codex-user", env={"USERPROFILE": str(fake_home)})
            self.assertEqual(result.returncode, 2)
            self.assertIn("--confirm-global", result.stdout)

    def test_db_add_list_show_and_sqlite_test(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            add = run_aiflow(cwd, "db", "add", "local", "--type", "sqlite", "--path", "data/local.db")
            self.assertEqual(add.returncode, 0, add.stderr)
            self.assertTrue((cwd / ".aiflow" / "databases.toml").exists())

            listing = run_aiflow(cwd, "db", "list")
            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertIn("local: sqlite", listing.stdout)

            show = run_aiflow(cwd, "db", "show", "local")
            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertIn('"type": "sqlite"', show.stdout)

            test = run_aiflow(cwd, "db", "test", "local")
            self.assertEqual(test.returncode, 0, test.stderr)
            self.assertTrue((cwd / "data" / "local.db").exists())

            conn = sqlite3.connect(cwd / "data" / "local.db")
            conn.execute("create table demo_item (id integer primary key)")
            conn.close()

            tables = run_aiflow(cwd, "db", "tables", "local")
            self.assertEqual(tables.returncode, 0, tables.stderr)
            self.assertIn("sqlite tables: 1", tables.stdout)
            self.assertIn("demo_item", tables.stdout)

    def test_db_query_runs_sqlite_select_and_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            add = run_aiflow(cwd, "db", "add", "local", "--type", "sqlite", "--path", "data/local.db")
            self.assertEqual(add.returncode, 0, add.stderr)

            create = run_aiflow(cwd, "db", "query", "local", "create table demo_item (id integer primary key, name text)")
            self.assertEqual(create.returncode, 0, create.stderr)
            self.assertIn("sqlite query affected:", create.stdout)

            insert = run_aiflow(cwd, "db", "query", "local", "insert into demo_item (name) values ('alpha'), ('beta')")
            self.assertEqual(insert.returncode, 0, insert.stderr)
            self.assertIn("sqlite query affected: 2", insert.stdout)

            select = run_aiflow(cwd, "db", "query", "local", "select id, name from demo_item order by id")
            self.assertEqual(select.returncode, 0, select.stderr)
            self.assertIn("sqlite query rows: 2", select.stdout)
            self.assertIn("id\tname", select.stdout)
            self.assertIn("1\talpha", select.stdout)
            self.assertIn("2\tbeta", select.stdout)

            limited = run_aiflow(cwd, "db", "query", "local", "select id, name from demo_item order by id", "--limit", "1")
            self.assertEqual(limited.returncode, 0, limited.stderr)
            self.assertIn("sqlite query rows: 1", limited.stdout)
            self.assertIn("1\talpha", limited.stdout)
            self.assertNotIn("2\tbeta", limited.stdout)

            json_result = run_aiflow(
                cwd,
                "db",
                "query",
                "local",
                "select id, name from demo_item order by id",
                "--format",
                "json",
            )
            self.assertEqual(json_result.returncode, 0, json_result.stderr)
            rows = json.loads(json_result.stdout)
            self.assertEqual(rows, [{"id": 1, "name": "alpha"}, {"id": 2, "name": "beta"}])

    def test_db_add_supports_sqlserver_driver_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            add = run_aiflow(
                cwd,
                "db",
                "add",
                "mssql",
                "--type",
                "sqlserver",
                "--host",
                "127.0.0.1",
                "--port",
                "1433",
                "--database",
                "app",
                "--driver",
                "ODBC Driver 18 for SQL Server",
            )
            self.assertEqual(add.returncode, 0, add.stderr)

            show = run_aiflow(cwd, "db", "show", "mssql")
            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertIn('"type": "sqlserver"', show.stdout)
            self.assertIn('"driver": "ODBC Driver 18 for SQL Server"', show.stdout)

    def test_db_refuses_plain_secret_without_local_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "db", "add", "dev", "--type", "postgres", "--dsn", "postgres://user:pass@localhost/db")
            self.assertEqual(result.returncode, 2)
            self.assertIn("Refusing to store database secrets", result.stdout)

    def test_nacos_add_show_get_and_write(self) -> None:
        requests: list[dict[str, str]] = []

        class NacosHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                parsed = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed.query)
                requests.append({key: values[0] for key, values in query.items()})
                if parsed.path != "/nacos/v1/cs/configs":
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"server.port=8080\nfeature.enabled=true\n")

            def log_message(self, format: str, *args: object) -> None:
                return

        server = HTTPServer(("127.0.0.1", 0), NacosHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                cwd = Path(tmp)
                base_url = f"http://127.0.0.1:{server.server_port}"
                add = run_aiflow(
                    cwd,
                    "nacos",
                    "add",
                    "dev",
                    "--server",
                    base_url,
                    "--namespace",
                    "public",
                    "--access-token",
                    "secret-token",
                    "--secret-local",
                )
                self.assertEqual(add.returncode, 0, add.stderr)
                self.assertTrue((cwd / ".aiflow" / "nacos.toml").exists())
                self.assertTrue((cwd / ".aiflow" / "nacos.local.toml").exists())
                self.assertNotIn("secret-token", (cwd / ".aiflow" / "nacos.toml").read_text(encoding="utf-8"))

                listing = run_aiflow(cwd, "nacos", "list")
                self.assertEqual(listing.returncode, 0, listing.stderr)
                self.assertIn("dev:", listing.stdout)
                self.assertIn("+ local secrets", listing.stdout)

                show = run_aiflow(cwd, "nacos", "show", "dev")
                self.assertEqual(show.returncode, 0, show.stderr)
                self.assertIn('"access_token_local": "***"', show.stdout)

                output = cwd / "out" / "app.properties"
                get = run_aiflow(
                    cwd,
                    "nacos",
                    "get",
                    "dev",
                    "--data-id",
                    "app.properties",
                    "--group",
                    "DEFAULT_GROUP",
                    "--output",
                    str(output),
                )
                self.assertEqual(get.returncode, 0, get.stderr)
                self.assertIn("server.port=8080", get.stdout)
                self.assertEqual(output.read_text(encoding="utf-8"), "server.port=8080\nfeature.enabled=true\n")
                self.assertEqual(requests[-1]["dataId"], "app.properties")
                self.assertEqual(requests[-1]["group"], "DEFAULT_GROUP")
                self.assertEqual(requests[-1]["tenant"], "public")
                self.assertEqual(requests[-1]["accessToken"], "secret-token")
        finally:
            server.shutdown()
            server.server_close()

    def test_nacos_refuses_plain_secret_without_local_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "nacos", "add", "dev", "--server", "http://127.0.0.1:8848", "--password", "secret")
            self.assertEqual(result.returncode, 2)
            self.assertIn("Refusing to store Nacos secrets", result.stdout)

    def test_wsl_run_dry_run_builds_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "wsl", "run", "--distro", "Ubuntu", "--user", "dev", "--cwd", "/repo", "--dry-run", "echo", "hello")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("wsl", result.stdout)
            self.assertIn("--distribution", result.stdout)
            self.assertIn("Ubuntu", result.stdout)
            self.assertIn("--user", result.stdout)
            self.assertIn("dev", result.stdout)
            self.assertIn("--cd", result.stdout)
            self.assertIn("/repo", result.stdout)
            self.assertIn("echo", result.stdout)
            self.assertIn("hello", result.stdout)

    def test_wsl_path_dry_run_builds_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "wsl", "path", "--to-wsl", "--dry-run", "C:\\Users\\demo")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("wslpath", result.stdout)
            self.assertIn("-u", result.stdout)
            self.assertIn("C:\\Users\\demo", result.stdout)

    def test_ssh_add_list_show_and_run_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            add = run_aiflow(
                cwd,
                "ssh",
                "add",
                "dev",
                "--host",
                "example.test",
                "--user",
                "deploy",
                "--port",
                "2222",
                "--key-path",
                "C:\\Users\\demo\\.ssh\\id_ed25519",
                "--secret-local",
                "--option",
                "StrictHostKeyChecking=no",
            )
            self.assertEqual(add.returncode, 0, add.stderr)
            self.assertTrue((cwd / ".aiflow" / "ssh.toml").exists())
            self.assertTrue((cwd / ".aiflow" / "ssh.local.toml").exists())
            self.assertNotIn("id_ed25519", (cwd / ".aiflow" / "ssh.toml").read_text(encoding="utf-8"))

            listing = run_aiflow(cwd, "ssh", "list")
            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertIn("dev: deploy@example.test:2222 + local secrets", listing.stdout)

            show = run_aiflow(cwd, "ssh", "show", "dev")
            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertIn('"key_path_local": "***"', show.stdout)

            dry_run = run_aiflow(cwd, "ssh", "run", "dev", "--dry-run", "uname", "-a")
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertIn("ssh", dry_run.stdout)
            self.assertIn("-p", dry_run.stdout)
            self.assertIn("2222", dry_run.stdout)
            self.assertIn("deploy@example.test", dry_run.stdout)
            self.assertIn("uname -a", dry_run.stdout)

    def test_ssh_refuses_plain_secret_without_local_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "ssh", "add", "dev", "--host", "example.test", "--key-path", "~/.ssh/id_ed25519")
            self.assertEqual(result.returncode, 2)
            self.assertIn("Refusing to store SSH secrets", result.stdout)


if __name__ == "__main__":
    unittest.main()

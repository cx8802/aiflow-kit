from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


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

    def test_frontend_install_dry_run_prints_project_local_playwright_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "frontend", "install", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("@playwright/test", result.stdout)
            self.assertIn("frontend-tools", result.stdout)
            self.assertIn("ms-playwright", result.stdout)
            self.assertIn("playwright", result.stdout)
            self.assertIn("would ensure .gitignore entries", result.stdout)

    def test_frontend_install_skip_browsers_uses_project_local_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            fake_bin = cwd / "fake-bin"
            fake_bin.mkdir()
            fake_npm = fake_bin / ("npm.cmd" if os.name == "nt" else "npm")
            if os.name == "nt":
                fake_npm.write_text("@echo off\necho fake npm %*\nexit /b 0\n", encoding="utf-8")
            else:
                fake_npm.write_text("#!/bin/sh\necho fake npm \"$@\"\n", encoding="utf-8")
                fake_npm.chmod(0o755)

            env = {"PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", "")}
            result = run_aiflow(cwd, "frontend", "install", "--skip-browsers", env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((cwd / ".tools" / "frontend-tools").exists())
            self.assertTrue((cwd / ".tools" / "ms-playwright").exists())
            gitignore = (cwd / ".gitignore").read_text(encoding="utf-8")
            self.assertIn(".tools/", gitignore)
            self.assertIn(".cache/", gitignore)

    def test_claude_agent_install_dry_run_uses_project_local_sdk_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "claude-agent", "install", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(".tools", result.stdout)
            self.assertIn("claude-agent", result.stdout)
            self.assertIn("@anthropic-ai/claude-agent-sdk", result.stdout)

    def test_claude_agent_run_dry_run_builds_read_only_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / ".aiflow").mkdir()
            (cwd / ".aiflow" / "context.compact.md").write_text("# Compact\n", encoding="utf-8")
            result = run_aiflow(cwd, "claude-agent", "run", "summarize", "commands", "--model", "test-model", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('"model": "test-model"', result.stdout)
            self.assertIn('"allowedTools"', result.stdout)
            self.assertIn('"Read"', result.stdout)
            self.assertIn('"disallowedTools"', result.stdout)
            self.assertIn('"Bash"', result.stdout)
            self.assertIn(".aiflow/context.compact.md", result.stdout)

    def test_claude_agent_run_requires_configured_alias_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_aiflow(cwd, "claude-agent", "run", "summarize", "--dry-run")
            self.assertEqual(result.returncode, 2)
            self.assertIn("claude_agent.small_model is empty", result.stdout)

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


if __name__ == "__main__":
    unittest.main()

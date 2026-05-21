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

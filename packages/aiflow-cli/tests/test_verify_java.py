from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aiflow.commands import verify


class JavaVerificationTests(unittest.TestCase):
    def test_platform_wrapper_detection_and_fallback(self):
        for platform in ("nt", "posix"):
            for marker in ("pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"):
                with self.subTest(platform=platform, marker=marker), tempfile.TemporaryDirectory(prefix="Java Projects ") as tmp:
                    root = Path(tmp)
                    (root / marker).touch()
                    maven = marker == "pom.xml"
                    base = "mvnw" if maven else "gradlew"
                    suffix = (".cmd" if maven else ".bat") if platform == "nt" else ""
                    fallback = "mvn test" if maven else "gradle test"
                    # A wrapper for the other platform must not suppress the PATH fallback.
                    other = base if platform == "nt" else base + (".cmd" if maven else ".bat")
                    (root / other).touch()
                    with patch.object(verify, "os", SimpleNamespace(name=platform)):
                        self.assertEqual(verify.detect_verify_commands(root), [("test", fallback)])
                        (root / (base + suffix)).touch()
                        prefix = ".\\" if platform == "nt" else "./"
                        self.assertEqual(verify.detect_verify_commands(root), [("test", prefix + base + suffix + " test")])

    def test_wrappers_execute_in_space_path_and_chain(self):
        # Runs native CMD batch files on Windows, native shell scripts on Unix.
        with tempfile.TemporaryDirectory(prefix="Java Projects ") as tmp:
            root = Path(tmp) / "John Doe" / "demo"
            root.mkdir(parents=True)
            (root / "pom.xml").touch()
            (root / "build.gradle.kts").touch()
            for base, suffix in (("mvnw", ".cmd"), ("gradlew", ".bat")):
                wrapper = root / (base + suffix if os.name == "nt" else base)
                if os.name == "nt":
                    script = f"@echo off\nif not \"%~1\"==\"test\" exit /b 17\necho %~1>{base}.ran\nexit /b 0\n"
                else:
                    script = f'#!/bin/sh\n[ "$1" = test ] || exit 17\nprintf "%s" "$1" > {base}.ran\n'
                wrapper.write_text(script, encoding="utf-8")
                wrapper.chmod(0o755)
            result = verify.run_verification(root, root / ".aiflow", auto=True)
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["exit_code"], 0)
            for base in ("mvnw", "gradlew"):
                self.assertEqual((root / (base + ".ran")).read_text().strip(), "test")

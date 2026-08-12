from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "preflight_runtime.py"


class PreflightRuntimeTests(unittest.TestCase):
    def test_missing_browser_is_a_hard_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "preflight.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--renderer",
                    "remotion",
                    "--ffmpeg",
                    "/usr/bin/true",
                    "--ffprobe",
                    "/usr/bin/true",
                    "--node",
                    "/usr/bin/true",
                    "--browser",
                    "/missing/browser",
                    "--report",
                    str(report),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("browser", result.stderr.lower())

    def test_explicit_local_binaries_produce_a_machine_readable_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "preflight.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--renderer",
                    "remotion",
                    "--ffmpeg",
                    "/usr/bin/true",
                    "--ffprobe",
                    "/usr/bin/true",
                    "--node",
                    "/usr/bin/true",
                    "--browser",
                    "/usr/bin/true",
                    "--report",
                    str(report),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(report.read_text(encoding="utf-8"))["passed"])


if __name__ == "__main__":
    unittest.main()

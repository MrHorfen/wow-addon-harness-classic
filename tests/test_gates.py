import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


class GateAndPackageTest(unittest.TestCase):
    def test_gate_passes(self):
        result = run("tools/gate.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_legacy_package(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run("tools/package.py", "--flavor", "legacy", "--out", temp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            toc = Path(temp) / "AHProbe-legacy" / "AHProbe" / "AHProbe.toc"
            text = toc.read_text(encoding="utf-8")
            self.assertIn("## Interface: 11509", text)
            self.assertIn("## Version: 0.1.0", text)
            self.assertTrue(
                (Path(temp) / "AHProbe-legacy" / "AHProbe" / "Core" / "Env.lua").is_file()
            )

    def test_modern_package(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run("tools/package.py", "--flavor", "modern", "--out", temp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            toc = Path(temp) / "AHProbe-modern" / "AHProbe" / "AHProbe.toc"
            text = toc.read_text(encoding="utf-8")
            self.assertIn("## Interface: 16001", text)
            self.assertIn("## Version: 0.1.0-modern", text)


if __name__ == "__main__":
    unittest.main()

import subprocess
import sys
import unittest


class TestMainModule(unittest.TestCase):
    def test_python_dash_m_invokes_cli(self):
        """
        `python -m extract_version` is a documented entry point (see
        CLAUDE.md), so it must actually dispatch to the CLI, not just import
        cleanly.
        """
        result = subprocess.run(
            [sys.executable, "-m", "extract_version", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()

import importlib
import subprocess
import sys
import unittest
from importlib.metadata import PackageNotFoundError, version
from unittest import mock

import extract_version


class TestPackageInit(unittest.TestCase):
    def test_version_matches_installed_metadata(self):
        """
        __version__ is read back from installed package metadata rather than
        being hardcoded, so it must always agree with importlib.metadata.
        """
        self.assertEqual(extract_version.__version__, version("extract_version"))

    def test_version_falls_back_when_package_not_installed(self):
        """
        If the package metadata can't be found (e.g. running from a source
        checkout that was never installed), __version__ falls back to "0.0.0"
        instead of raising.
        """
        with mock.patch("importlib.metadata.version", side_effect=PackageNotFoundError):
            importlib.reload(extract_version)
            self.assertEqual(extract_version.__version__, "0.0.0")
        importlib.reload(extract_version)

    def test_package_root_and_project_dir(self):
        self.assertTrue(extract_version.PACKAGE_ROOT.is_dir())
        self.assertEqual(extract_version.PACKAGE_ROOT.name, "extract_version")
        self.assertEqual(extract_version.PROJECT_DIR, extract_version.PACKAGE_ROOT.parent)


class TestMainModule(unittest.TestCase):
    def test_main_module_exposes_cli_main(self):
        import extract_version.__main__ as main_module

        self.assertTrue(callable(main_module.main))

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

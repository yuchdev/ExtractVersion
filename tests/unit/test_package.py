import unittest
from importlib.metadata import version

import extract_version


class TestPackageInit(unittest.TestCase):
    def test_version_matches_installed_metadata(self):
        """
        __version__ is read back from installed package metadata rather than
        being hardcoded, so it must always agree with importlib.metadata.
        """
        self.assertEqual(extract_version.__version__, version("extract_version"))

    def test_package_root_and_project_dir(self):
        self.assertTrue(extract_version.PACKAGE_ROOT.is_dir())
        self.assertEqual(extract_version.PACKAGE_ROOT.name, "extract_version")
        self.assertEqual(extract_version.PROJECT_DIR, extract_version.PACKAGE_ROOT.parent)


class TestMainModule(unittest.TestCase):
    def test_main_module_exposes_cli_main(self):
        import extract_version.__main__ as main_module

        self.assertTrue(callable(main_module.main))


if __name__ == "__main__":
    unittest.main()

import importlib
import unittest
from importlib.metadata import PackageNotFoundError
from unittest import mock

import extract_version


class TestPackageInit(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

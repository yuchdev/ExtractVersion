import os
import tempfile
import unittest

from extract_version.version_info import (
    available_versions,
    get_last_version,
)


class TestVersionInfoFilesystem(unittest.TestCase):
    """
    available_versions()/get_last_version() against real, checked-in fixture directories
    under test_data/versions/, plus the versions_path-vs-versions_list precedence rule
    (including its empty-directory boundary via a real temp dir).
    """

    def test_available_versions(self):
        """
        Test all available versions of application
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_version_dirs = {
            "../test_data/versions/cellar": {
                "pattern": "(.*)",
                "expected": {"0.01": "0.01", "1.0": "1.0", "0.87": "0.87"},
            },
            "../test_data/versions/pycharm": {
                "pattern": "PyCharm(.*)",
                "expected": {"2020.3": "PyCharm2020.3", "2021.1": "PyCharm2021.1", "2020.1": "PyCharm2020.1"},
            },
        }
        for versions_path, data in test_version_dirs.items():
            full_versions_path = os.path.join(current_dir, versions_path)
            all_versions = available_versions(versions_path=full_versions_path, pattern=data["pattern"])
            expected_all_versions = data["expected"]
            self.assertEqual(all_versions, expected_all_versions)

    def test_get_last_version(self):
        """
        Test last version directory
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_version_dirs = {
            "../test_data/versions/cellar": {"pattern": "(.*)", "expected": "1.0"},
            "../test_data/versions/pycharm": {"pattern": "PyCharm(.*)", "expected": "PyCharm2021.1"},
        }
        for versions_path, data in test_version_dirs.items():
            full_versions_path = os.path.join(current_dir, versions_path)
            last_version = get_last_version(versions_list=os.listdir(full_versions_path), pattern=data["pattern"])
            expected_last_version_dir = data["expected"]
            self.assertEqual(last_version, expected_last_version_dir)

    def test_available_versions_from_path_filters_unparseable(self):
        """
        Test that the versions_path (os.listdir) source applies the same
        invalid-entry filtering as the versions_list source: a directory holding
        both valid version-named entries and non-version names ("NoVersion",
        "latest") yields only the valid ones, with no "" key leaking in
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mixed_path = os.path.join(current_dir, "../test_data/versions/mixed")
        result = available_versions(versions_path=mixed_path)
        self.assertEqual(result, {"1.0": "1.0", "2.0.0": "2.0.0"})
        self.assertNotIn("", result)
        # get_last_version over the same filesystem source returns the newest
        # valid entry, ignoring the unparseable directory names entirely
        self.assertEqual(get_last_version(versions_path=mixed_path), "2.0.0")

    def test_available_versions_from_path_all_unparseable_is_empty(self):
        """
        Test the filesystem-source parity of the all-invalid boundary already
        pinned for the list source: a directory in which no entry yields a
        version maps to an empty dict via available_versions() and makes
        get_last_version() raise a descriptive ValueError, so a mutation that
        filtered differently (or crashed) on an all-invalid os.listdir() result
        would be caught here too
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        all_invalid_path = os.path.join(current_dir, "../test_data/versions/all-invalid")
        self.assertEqual(available_versions(versions_path=all_invalid_path), {})
        with self.assertRaises(ValueError) as context:
            get_last_version(versions_path=all_invalid_path)
        self.assertIn("no valid version found", str(context.exception))

    def test_get_last_version_from_path_returns_original_dir_name(self):
        """
        Test that the filtering versions_path source returns the original
        directory name, not the normalized version key: this fixture mixes
        unparseable names with valid entries whose directory names differ from
        their extracted versions ("app-1.0" -> "1.0", "app-2.0.0" -> "2.0.0"),
        so a mutation returning the sorted version key ("2.0.0") instead of the
        winning directory name ("app-2.0.0") is caught here
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filtered_path = os.path.join(current_dir, "../test_data/versions/filtered")
        self.assertEqual(
            available_versions(versions_path=filtered_path),
            {"1.0": "app-1.0", "2.0.0": "app-2.0.0"},
        )
        self.assertEqual(get_last_version(versions_path=filtered_path), "app-2.0.0")

    def test_duplicate_normalized_winner_stable_across_sources(self):
        """
        Test the Compatibility Policy stance on duplicate normalized versions:
        when two entries normalize to the same key ("1.0" and "1.0.0" both pad
        to (1, 0, 0)), the winner is a pure function of the version strings and
        is identical whether sourced via versions_list or via versions_path
        (os.listdir())
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        duplicates_path = os.path.join(current_dir, "../test_data/versions/duplicates")
        from_path = get_last_version(versions_path=duplicates_path)
        from_list = get_last_version(versions_list=os.listdir(duplicates_path))
        self.assertEqual(from_path, from_list)
        # "1.0" and "1.0.0" tie on (1, 0, 0); string tie-break makes "1.0.0" win
        self.assertEqual(from_path, "1.0.0")

    def test_versions_path_wins_over_versions_list(self):
        """
        Test the documented precedence rule: when both versions_path and
        versions_list are passed, versions_path (os.listdir) wins and the
        versions_list argument is ignored entirely -- the result reflects the
        fixture directory's contents, never the "9.9.9" sentinel or a merge of
        the two sources. This pins a mutation-survivable gap (a mutation that
        merged both inputs, or preferred versions_list, would be caught here).
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cellar_path = os.path.join(current_dir, "../test_data/versions/cellar")
        # available_versions(): both sources supplied, path wins.
        result = available_versions(
            versions_path=cellar_path,
            versions_list=["9.9.9"],
            pattern="(.*)",
        )
        self.assertEqual(result, {"0.01": "0.01", "0.87": "0.87", "1.0": "1.0"})
        self.assertNotIn("9.9.9", result)
        # get_last_version(): same precedence, newest entry from the directory,
        # not the ignored "9.9.9" sentinel from versions_list.
        last_version = get_last_version(
            versions_path=cellar_path,
            versions_list=["9.9.9"],
            pattern="(.*)",
        )
        self.assertEqual(last_version, "1.0")

    def test_empty_versions_path_wins_over_versions_list(self):
        """
        Test that the precedence rule is unconditional: an EMPTY versions_path
        still wins over a non-empty versions_list, rather than silently falling
        back to the list. available_versions() must return {} and
        get_last_version() must raise its descriptive ValueError, proving the
        list data is never consulted once a path is given. Uses a temp dir
        because git cannot track an empty fixture directory.
        """
        with tempfile.TemporaryDirectory() as empty_path:
            self.assertEqual(
                available_versions(versions_path=empty_path, versions_list=["9.9.9"]),
                {},
            )
            with self.assertRaises(ValueError) as context:
                get_last_version(versions_path=empty_path, versions_list=["9.9.9"])
            self.assertIn("no valid version found", str(context.exception))


if __name__ == "__main__":
    unittest.main()

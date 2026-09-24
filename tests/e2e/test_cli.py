import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout

from extract_version import cli


def run_cli(argv):
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        exit_code = cli.main(argv)
    return exit_code, stdout.getvalue(), stderr.getvalue()


class TestCliDirectoryCommands(unittest.TestCase):
    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        versions_root = os.path.join(current_dir, "../test_data/versions")
        self.cellar_dir = os.path.join(versions_root, "cellar")
        self.pycharm_dir = os.path.join(versions_root, "pycharm")
        self.mixed_dir = os.path.join(versions_root, "mixed")
        self.all_invalid_dir = os.path.join(versions_root, "all-invalid")
        self.filtered_dir = os.path.join(versions_root, "filtered")
        self.duplicates_dir = os.path.join(versions_root, "duplicates")
        # A --path that does not exist (FileNotFoundError) and one that points at
        # an existing file rather than a directory (NotADirectoryError); both
        # surface from os.listdir() as OSError subclasses.
        self.nonexistent_dir = os.path.join(versions_root, "no-such-directory-xyz")
        self.not_a_directory = os.path.join(current_dir, "test_cli.py")

    def test_available_with_path(self):
        exit_code, out, _ = run_cli(["available", "--path", self.cellar_dir, "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(out), {"0.01": "0.01", "1.0": "1.0", "0.87": "0.87"})

    def test_available_with_path_plain_text(self):
        """
        Without --json, available prints one tab-separated "version\\tname" line
        per entry, ordered by the numeric version-sort contract in _print. Pins the
        exact plain-text layout, which every other available test skips via --json.
        (Here numeric and lexicographic order coincide; the multi-digit ordering
        tests below cover the case where they diverge.)
        """
        exit_code, out, _ = run_cli(["available", "--path", self.cellar_dir])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "0.01\t0.01\n0.87\t0.87\n1.0\t1.0\n")

    def test_available_with_names_and_pattern(self):
        names = os.listdir(self.pycharm_dir)
        exit_code, out, _ = run_cli(["available", *names, "--pattern", "PyCharm(.*)", "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(out),
            {"2020.3": "PyCharm2020.3", "2021.1": "PyCharm2021.1", "2020.1": "PyCharm2020.1"},
        )

    def test_last_version_with_path(self):
        exit_code, out, _ = run_cli(["last-version", "--path", self.pycharm_dir, "--pattern", "PyCharm(.*)"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "PyCharm2021.1\n")

    def test_last_version_json_scalar_is_quoted_string(self):
        """
        last-version --json takes _print's scalar branch: the winning name is
        serialized via json.dumps(), so it is a quoted JSON string
        (``"PyCharm2021.1"``) rather than the bare plain-text line. This is the
        only command whose scalar --json shape was previously untested.
        """
        exit_code, out, _ = run_cli(["last-version", "--path", self.pycharm_dir, "--pattern", "PyCharm(.*)", "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, '"PyCharm2021.1"\n')
        self.assertEqual(json.loads(out), "PyCharm2021.1")

    def test_available_path_wins_over_positional_names(self):
        """
        When both --path and positional NAME(s) are given, _versions_source
        gives --path priority: the inventory reflects the fixture directory's
        contents, and the ignored positional name never appears in the result.
        """
        exit_code, out, _ = run_cli(["available", "--path", self.cellar_dir, "ignored-positional-9.9.9", "--json"])
        self.assertEqual(exit_code, 0)
        result = json.loads(out)
        self.assertEqual(result, {"0.01": "0.01", "1.0": "1.0", "0.87": "0.87"})
        self.assertNotIn("9.9.9", result)
        self.assertNotIn("ignored-positional-9.9.9", result.values())

    def test_last_version_path_wins_over_positional_names(self):
        """
        last-version applies the same --path-over-positional precedence: the
        winner is drawn from the fixture directory, not the (numerically larger)
        positional name that would otherwise win if it were considered.
        """
        exit_code, out, _ = run_cli(["last-version", "--path", self.cellar_dir, "ignored-positional-9.9.9"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "1.0\n")

    def test_available_with_path_mixed_valid_and_invalid(self):
        """
        The mixed/ fixture holds valid version dirs ("1.0", "2.0.0") alongside
        unparseable ones ("NoVersion", "latest"); available --path keeps only the
        valid entries, mirroring the library-level filtering test, and exits 0.
        """
        exit_code, out, _ = run_cli(["available", "--path", self.mixed_dir, "--json"])
        self.assertEqual(exit_code, 0)
        result = json.loads(out)
        self.assertEqual(result, {"1.0": "1.0", "2.0.0": "2.0.0"})
        self.assertNotIn("", result)

    def test_last_version_with_path_mixed_valid_and_invalid(self):
        """
        last-version --path on the mixed/ fixture returns the newest valid entry
        ("2.0.0"), ignoring the unparseable directory names entirely, exit 0.
        """
        exit_code, out, _ = run_cli(["last-version", "--path", self.mixed_dir])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "2.0.0\n")

    def test_available_with_path_all_invalid_empty_inventory(self):
        """
        The all-invalid/ fixture yields an empty inventory via available --path:
        empty JSON with exit 1, matching the all-unparseable list-input case.
        """
        exit_code, out, _ = run_cli(["available", "--path", self.all_invalid_dir, "--json"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(json.loads(out), {})

    def test_available_with_path_all_invalid_plain_text_empty_stdout(self):
        """
        The all-invalid/ fixture yields an empty inventory in plain-text mode
        (no --json): available --path exits 1 with EMPTY stdout, because the
        plain-text mapping loop in _print simply never iterates over an empty
        dict (the empty-inventory case was previously only covered via --json).
        """
        exit_code, out, _ = run_cli(["available", "--path", self.all_invalid_dir])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")

    def test_last_version_with_path_all_invalid_friendly_error(self):
        """
        last-version --path on the all-invalid/ fixture exits 1 with the friendly
        stderr message and empty stdout, never an uncaught error.
        """
        exit_code, out, err = run_cli(["last-version", "--path", self.all_invalid_dir])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("no version found in the given input", err)

    def test_available_with_path_filtered_returns_original_dir_names(self):
        """
        The filtered/ fixture holds valid entries whose directory names differ
        from their extracted version keys ("app-1.0" -> "1.0",
        "app-2.0.0" -> "2.0.0"); available --path maps each version key to the
        original directory name, and drops the unparseable entries.
        """
        exit_code, out, _ = run_cli(["available", "--path", self.filtered_dir, "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(out), {"1.0": "app-1.0", "2.0.0": "app-2.0.0"})

    def test_last_version_with_path_filtered_returns_original_dir_name(self):
        """
        last-version --path on the filtered/ fixture returns the winning original
        directory name ("app-2.0.0"), not the normalized version key ("2.0.0").
        """
        exit_code, out, _ = run_cli(["last-version", "--path", self.filtered_dir])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "app-2.0.0\n")

    def test_available_with_path_duplicates(self):
        """
        The duplicates/ fixture holds "1.0" and "1.0.0", which normalize to the
        same numeric key but stay distinct string keys in the inventory; both are
        listed via available --path, exit 0.
        """
        exit_code, out, _ = run_cli(["available", "--path", self.duplicates_dir, "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(out), {"1.0": "1.0", "1.0.0": "1.0.0"})

    def test_last_version_with_path_duplicates_deterministic_tie_break(self):
        """
        last-version --path on the duplicates/ fixture resolves the "1.0" vs
        "1.0.0" tie (both pad to (1, 0, 0)) deterministically to "1.0.0" via the
        string tie-break, mirroring the library-level cross-source stability test.
        """
        exit_code, out, _ = run_cli(["last-version", "--path", self.duplicates_dir])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "1.0.0\n")

    def test_available_nonexistent_path_friendly_error(self):
        """
        A nonexistent --path raises FileNotFoundError from os.listdir(); the CLI
        must catch it as an OSError and report a friendly stderr message with
        exit 1, never a raw Python traceback.
        """
        exit_code, out, err = run_cli(["available", "--path", self.nonexistent_dir])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("extract-version available:", err)
        self.assertIn("no-such-directory-xyz", err)
        self.assertNotIn("Traceback", err)

    def test_available_path_not_a_directory_friendly_error(self):
        """
        A --path pointing at an existing file (not a directory) raises
        NotADirectoryError from os.listdir(); the CLI reports it as a friendly
        stderr message with exit 1, never a raw traceback.
        """
        exit_code, out, err = run_cli(["available", "--path", self.not_a_directory])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("extract-version available:", err)
        self.assertNotIn("Traceback", err)

    def test_last_version_nonexistent_path_friendly_error(self):
        """
        A nonexistent --path raises FileNotFoundError from os.listdir(); the CLI
        must catch it as an OSError and report a friendly stderr message with
        exit 1, never a raw Python traceback.
        """
        exit_code, out, err = run_cli(["last-version", "--path", self.nonexistent_dir])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("extract-version last-version:", err)
        self.assertIn("no-such-directory-xyz", err)
        self.assertNotIn("Traceback", err)

    def test_last_version_path_not_a_directory_friendly_error(self):
        """
        A --path pointing at an existing file (not a directory) raises
        NotADirectoryError from os.listdir(); the CLI reports it as a friendly
        stderr message with exit 1, never a raw traceback.
        """
        exit_code, out, err = run_cli(["last-version", "--path", self.not_a_directory])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("extract-version last-version:", err)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()

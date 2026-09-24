import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from extract_version import cli


class StdinPipe(io.StringIO):
    """A StringIO that reports itself as piped (not a TTY), like a real pipe."""

    def isatty(self):
        return False


class StdinTty(io.StringIO):
    """A StringIO that reports itself as a TTY, like an interactive terminal
    with nothing piped in."""

    def isatty(self):
        return True


def run_cli(argv):
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        exit_code = cli.main(argv)
    return exit_code, stdout.getvalue(), stderr.getvalue()


class TestCliExtract(unittest.TestCase):
    def test_extract_plain(self):
        exit_code, out, _ = run_cli(["extract", "PyCharm-2018.1.2-linux"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "2018.1.2\n")

    def test_extract_json(self):
        exit_code, out, _ = run_cli(["extract", "PyCharm-2018.1.2-linux", "my_program_v1.0", "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(out), ["2018.1.2", "1.0"])

    def test_extract_with_pattern(self):
        exit_code, out, _ = run_cli(
            ["extract", "PyCharm-2018.1.2-windows-10.0", "--pattern", "PyCharm-(.*)-windows-10.0"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "2018.1.2\n")

    def test_extract_no_match(self):
        exit_code, out, err = run_cli(["extract", "NoVersionHere"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("NoVersionHere", err)

    def test_extract_no_input(self):
        with mock.patch.object(cli.sys, "stdin", StdinPipe("")):
            exit_code, out, err = run_cli(["extract"])
        self.assertEqual(exit_code, 2)
        self.assertIn("no input given", err)

    def test_extract_from_stdin(self):
        with mock.patch.object(cli.sys, "stdin", StdinPipe("PyCharm-2018.1.2\nmy_program_v1.0\n")):
            exit_code, out, _ = run_cli(["extract"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "2018.1.2\n1.0\n")

    def test_extract_no_input_interactive_tty(self):
        """
        With no positional names and no piped stdin (an interactive TTY),
        _read_names() takes its "nothing to read" branch rather than
        blocking on stdin, so the CLI reports the same "no input given"
        error as the empty-pipe case.
        """
        with mock.patch.object(cli.sys, "stdin", StdinTty("")):
            exit_code, out, err = run_cli(["extract"])
        self.assertEqual(exit_code, 2)
        self.assertIn("no input given", err)

    def test_extract_pattern_no_capture_group_friendly_error(self):
        """A capture-group-less pattern exits nonzero with a friendly stderr, not a traceback."""
        exit_code, out, err = run_cli(["extract", "PyCharm-2018.1.2", "--pattern", "PyCharm-.*"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("capture group", err)
        self.assertNotIn("Traceback", err)

    def test_extract_pattern_invalid_regex_friendly_error(self):
        """An invalid regex pattern exits nonzero with a friendly stderr, not a traceback."""
        exit_code, out, err = run_cli(["extract", "PyCharm-2018.1.2", "--pattern", "PyCharm-("])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("extract-version extract:", err)
        self.assertNotIn("Traceback", err)

    def test_extract_mixed_valid_and_invalid_partial_failure(self):
        """
        A single call mixing an extractable and an unextractable name is a
        partial failure: exit 1, yet the extracted version is still printed to
        stdout while the failing name is reported on stderr (partial-success,
        explicitly not all-or-nothing).
        """
        exit_code, out, err = run_cli(["extract", "PyCharm-2018.1.2-linux", "NoVersionHere"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "2018.1.2\n")
        self.assertIn("NoVersionHere", err)

    def test_extract_multi_name_pattern_error_short_circuits(self):
        """
        In a multi-name batch, a pattern error on any name short-circuits the
        whole command: _cmd_extract returns from its except branch before _print
        runs, so no partial results are flushed. Stdout stays empty (exit 1),
        even though both names would otherwise match the pattern.
        """
        exit_code, out, err = run_cli(["extract", "PyCharm-2018.1.2", "PyCharm-2019.1.2", "--pattern", "PyCharm-.*"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("capture group", err)
        self.assertNotIn("Traceback", err)


class TestCliValidate(unittest.TestCase):
    def test_validate_valid(self):
        exit_code, out, _ = run_cli(["validate", "0.87", "1.00"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "0.87\n1.00\n")

    def test_validate_invalid(self):
        exit_code, out, err = run_cli(["validate", "NoVersion"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("NoVersion", err)

    def test_validate_rejects_valid_prefix_with_junk(self):
        """
        Strings that begin with a valid-looking version but carry trailing
        garbage (accepted by the old prefix-based validate) are now rejected:
        exit 1, empty stdout, every name echoed to stderr.
        """
        near_misses = ["1.0.0abc", "1.0beta", "1.0.0-linux"]
        exit_code, out, err = run_cli(["validate", *near_misses])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        for name in near_misses:
            self.assertIn(name, err)

    def test_validate_no_input(self):
        """
        Empty piped input reports no input (exit 2), matching every other
        subcommand's no-input branch, rather than silently succeeding.
        """
        with mock.patch.object(cli.sys, "stdin", StdinPipe("")):
            exit_code, out, err = run_cli(["validate"])
        self.assertEqual(exit_code, 2)
        self.assertIn("no input given", err)

    def test_validate_mixed_valid_and_invalid_partial_failure(self):
        """
        A single call mixing valid and invalid names is a partial failure:
        exit 1, yet the valid results are still printed to stdout while the
        invalid name is reported on stderr.
        """
        exit_code, out, err = run_cli(["validate", "1.0", "NoVersion"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "1.0\n")
        self.assertIn("NoVersion", err)

    def test_validate_json_valid(self):
        """
        validate --json serializes its successful results as a JSON array, the
        same list shape the plain-text mode prints one-per-line. This is the
        only command family whose --json output structure was previously
        untested.
        """
        exit_code, out, _ = run_cli(["validate", "0.87", "1.00", "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(out), ["0.87", "1.00"])

    def test_validate_json_partial_failure_only_successes_on_stdout(self):
        """
        With --json a mixed valid/invalid call still keeps the two streams
        separate: only the valid result is serialized into the stdout JSON
        array while the invalid name is reported on stderr, exit 1. No error
        placeholder leaks into the array.
        """
        exit_code, out, err = run_cli(["validate", "1.0", "NoVersion", "--json"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(json.loads(out), ["1.0"])
        self.assertIn("NoVersion", err)

    def test_validate_two_invalid_names_emit_exactly_one_stderr_line_each(self):
        """
        The documented "one stderr line per failed name" fan-out is pinned by
        count: two invalid names must produce exactly two stderr lines, one
        naming each failed input. Guards against a regression collapsing
        failures into a single line, duplicating a line, or emitting a spurious
        extra one (which the substring-only partial-failure tests would miss).
        """
        exit_code, out, err = run_cli(["validate", "NoVersion", "AlsoBad"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        lines = err.strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("NoVersion", lines[0])
        self.assertIn("AlsoBad", lines[1])


class TestCliSort(unittest.TestCase):
    def test_sort_ascending(self):
        exit_code, out, _ = run_cli(["sort", "20", "1.0", "1.0.2", "1.0.1", "10"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "1.0\n1.0.1\n1.0.2\n10\n20\n")

    def test_sort_descending_json(self):
        exit_code, out, _ = run_cli(["sort", "1.0", "2.0", "1.5", "--descending", "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(out), ["2.0", "1.5", "1.0"])

    def test_sort_from_stdin(self):
        with mock.patch.object(cli.sys, "stdin", StdinPipe("1.0.2\n1.0\n1.0.1\n")):
            exit_code, out, _ = run_cli(["sort"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "1.0\n1.0.1\n1.0.2\n")

    def test_sort_invalid_entry_semantic_failure(self):
        """
        A single unparseable entry fails the whole sort (all-or-nothing, per
        sort_versions()'s contract): exit 1, empty stdout, one stderr line
        naming the command and the invalid entry.
        """
        exit_code, out, err = run_cli(["sort", "1.0", "NoVersion"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("extract-version sort:", err)
        self.assertIn("NoVersion", err)
        self.assertNotIn("Traceback", err)

    def test_sort_no_input(self):
        with mock.patch.object(cli.sys, "stdin", StdinPipe("")):
            exit_code, out, err = run_cli(["sort"])
        self.assertEqual(exit_code, 2)
        self.assertIn("no input given", err)


class TestCliDirectoryCommands(unittest.TestCase):
    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        versions_root = os.path.join(current_dir, "test_data/versions")
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

    def test_available_plain_text_numeric_not_lexicographic_order(self):
        """
        With multi-digit segments where lexicographic and numeric order diverge
        ("1.9" vs "1.10", "2.0" vs "10.0"), available's plain-text output follows
        the numeric version-sort contract: "1.9" precedes "1.10" (lexicographic
        string order would wrongly put "1.10" first).
        """
        exit_code, out, _ = run_cli(["available", "1.10", "1.9", "10.0", "2.0"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "1.9\t1.9\n1.10\t1.10\n2.0\t2.0\n10.0\t10.0\n")

    def test_available_plain_text_numeric_order_binds_correct_name(self):
        """
        With --pattern the extracted version differs from the original name, so
        this pins both halves of _print's ordering contract at once: the versions
        come out in numeric order ("1.9" before "1.10", not lexicographic) AND
        each version stays bound to the name it was extracted from ("1.9" ->
        "app-1.9"). The other divergence tests use key == name, and the JSON tests
        assert via json.loads() which discards order, so neither can catch a
        mutation that reorders keys but reattaches the wrong name.
        """
        exit_code, out, _ = run_cli(["available", "app-1.10", "app-1.9", "--pattern", "app-(.*)"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "1.9\tapp-1.9\n1.10\tapp-1.10\n")

    def test_available_json_numeric_not_lexicographic_order(self):
        """
        The --json object serializes its keys in the same numeric version order
        as the plain-text lines ("1.9" before "1.10", "2.0" before "10.0"), not
        lexicographically. json.loads() would discard order, so assert on the raw
        key sequence.
        """
        exit_code, out, _ = run_cli(["available", "1.10", "1.9", "10.0", "2.0", "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(list(json.loads(out).keys()), ["1.9", "1.10", "2.0", "10.0"])

    def test_available_with_names_and_pattern(self):
        names = os.listdir(self.pycharm_dir)
        exit_code, out, _ = run_cli(["available", *names, "--pattern", "PyCharm(.*)", "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(out),
            {"2020.3": "PyCharm2020.3", "2021.1": "PyCharm2021.1", "2020.1": "PyCharm2020.1"},
        )

    def test_available_no_input(self):
        with mock.patch.object(cli.sys, "stdin", StdinPipe("")):
            exit_code, out, err = run_cli(["available"])
        self.assertEqual(exit_code, 2)
        self.assertIn("no input given", err)

    def test_last_version_with_path(self):
        exit_code, out, _ = run_cli(["last-version", "--path", self.pycharm_dir, "--pattern", "PyCharm(.*)"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "PyCharm2021.1\n")

    def test_last_version_from_stdin(self):
        names = os.listdir(self.pycharm_dir)
        with mock.patch.object(cli.sys, "stdin", StdinPipe("\n".join(names) + "\n")):
            exit_code, out, _ = run_cli(["last-version", "--pattern", "PyCharm(.*)"])
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

    def test_available_filters_unparseable_names(self):
        """A mix of valid and unparseable names yields no blank-key row."""
        exit_code, out, _ = run_cli(["available", "1.0", "NoVersion", "PyCharm-2020.1.0", "--json"])
        self.assertEqual(exit_code, 0)
        result = json.loads(out)
        self.assertEqual(result, {"1.0": "1.0", "2020.1.0": "PyCharm-2020.1.0"})
        self.assertNotIn("", result)

    def test_available_all_unparseable_exits_nonzero(self):
        """All-unparseable input maps to an empty inventory and exits 1."""
        exit_code, out, _ = run_cli(["available", "NoVersion", "beta", "1", "--json"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(json.loads(out), {})

    def test_last_version_all_unparseable_friendly_error(self):
        """All-unparseable input exits cleanly with the friendly stderr message."""
        exit_code, out, err = run_cli(["last-version", "NoVersion", "beta", "1"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("no version found in the given input", err)

    def test_last_version_empty_stdin_friendly_error(self):
        """Empty piped input reports no input (exit 2), never an uncaught error."""
        with mock.patch.object(cli.sys, "stdin", StdinPipe("")):
            exit_code, out, err = run_cli(["last-version"])
        self.assertEqual(exit_code, 2)
        self.assertIn("no input given", err)

    def test_available_pattern_no_capture_group_friendly_error(self):
        """A capture-group-less pattern exits nonzero with a friendly stderr, not a traceback."""
        exit_code, out, err = run_cli(["available", "PyCharm-2020.1.0", "--pattern", "PyCharm-.*"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("capture group", err)
        self.assertNotIn("Traceback", err)

    def test_available_pattern_invalid_regex_friendly_error(self):
        """An invalid regex pattern exits nonzero with a friendly stderr, not a traceback."""
        exit_code, out, err = run_cli(["available", "PyCharm-2020.1.0", "--pattern", "PyCharm-("])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("extract-version available:", err)
        self.assertNotIn("Traceback", err)

    def test_last_version_pattern_no_capture_group_friendly_error(self):
        """A capture-group-less pattern exits nonzero with a friendly stderr, not a traceback."""
        exit_code, out, err = run_cli(["last-version", "PyCharm-2020.1.0", "--pattern", "PyCharm-.*"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("capture group", err)
        self.assertNotIn("Traceback", err)

    def test_last_version_pattern_invalid_regex_friendly_error(self):
        """An invalid regex pattern exits nonzero with a friendly stderr, not a traceback."""
        exit_code, out, err = run_cli(["last-version", "PyCharm-2020.1.0", "--pattern", "PyCharm-("])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("extract-version last-version:", err)
        self.assertNotIn("Traceback", err)

    def test_last_version_pattern_captures_invalid_reports_no_version(self):
        """
        A well-formed single-capture pattern whose capture is unparseable reaches
        the "no valid version" branch and must route to the "no version found"
        message, not the "capture group" one (guards the string-based routing in
        _cmd_last_version's except clause).
        """
        exit_code, out, err = run_cli(["last-version", "PyCharm-abc", "--pattern", "PyCharm-(.*)"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out, "")
        self.assertIn("no version found", err)
        self.assertNotIn("capture group", err)

    def test_available_pattern_captures_invalid_empty_inventory(self):
        """
        A well-formed single-capture pattern whose capture is unparseable for
        every name yields an empty inventory and exits 1 with empty JSON.
        """
        exit_code, out, _ = run_cli(["available", "PyCharm-abc", "--pattern", "PyCharm-(.*)", "--json"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(json.loads(out), {})

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


class TestCliArgparseErrors(unittest.TestCase):
    """
    argparse's own exit-2 path (unknown subcommand / missing required
    subcommand) is distinct from the hand-rolled ``return 2`` no-input
    branches: argparse raises ``SystemExit(2)`` from inside ``main`` rather
    than returning a value, so ``run_cli`` never gets to return its tuple and
    the exception must be caught around the call.
    """

    def test_unknown_subcommand_exits_2(self):
        with self.assertRaises(SystemExit) as ctx:
            run_cli(["bogus"])
        self.assertEqual(ctx.exception.code, 2)

    def test_missing_subcommand_exits_2(self):
        with self.assertRaises(SystemExit) as ctx:
            run_cli([])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

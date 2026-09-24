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
    """
    Stdin-mocked cases for the extract subcommand.
    """

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


class TestCliValidate(unittest.TestCase):
    """
    Stdin-mocked cases for the validate subcommand.
    """

    def test_validate_no_input(self):
        """
        Empty piped input reports no input (exit 2), matching every other
        subcommand's no-input branch, rather than silently succeeding.
        """
        with mock.patch.object(cli.sys, "stdin", StdinPipe("")):
            exit_code, out, err = run_cli(["validate"])
        self.assertEqual(exit_code, 2)
        self.assertIn("no input given", err)


class TestCliSort(unittest.TestCase):
    """
    Stdin-mocked cases for the sort subcommand.
    """

    def test_sort_from_stdin(self):
        with mock.patch.object(cli.sys, "stdin", StdinPipe("1.0.2\n1.0\n1.0.1\n")):
            exit_code, out, _ = run_cli(["sort"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "1.0\n1.0.1\n1.0.2\n")

    def test_sort_no_input(self):
        with mock.patch.object(cli.sys, "stdin", StdinPipe("")):
            exit_code, out, err = run_cli(["sort"])
        self.assertEqual(exit_code, 2)
        self.assertIn("no input given", err)


class TestCliAvailableLastVersionStdin(unittest.TestCase):
    """
    Stdin-mocked cases for available/last-version, including the piped-names success path
    sourced from the real pycharm/ fixture.
    """

    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.pycharm_dir = os.path.join(current_dir, "..", "test_data", "versions", "pycharm")


    def test_available_from_stdin(self):
        """
        available's stdin fallback (via _read_names / _versions_source when no
        --path and no positional NAMEs) builds the inventory from piped names,
        mirroring last-version's stdin path. Without this, available's non-path,
        non-positional success branch was never exercised.
        """
        names = os.listdir(self.pycharm_dir)
        with mock.patch.object(cli.sys, "stdin", StdinPipe("\n".join(names) + "\n")):
            exit_code, out, _ = run_cli(["available", "--pattern", "PyCharm(.*)", "--json"])
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

    def test_last_version_from_stdin(self):
        names = os.listdir(self.pycharm_dir)
        with mock.patch.object(cli.sys, "stdin", StdinPipe("\n".join(names) + "\n")):
            exit_code, out, _ = run_cli(["last-version", "--pattern", "PyCharm(.*)"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "PyCharm2021.1\n")

    def test_last_version_empty_stdin_friendly_error(self):
        """Empty piped input reports no input (exit 2), never an uncaught error."""
        with mock.patch.object(cli.sys, "stdin", StdinPipe("")):
            exit_code, out, err = run_cli(["last-version"])
        self.assertEqual(exit_code, 2)
        self.assertIn("no input given", err)


class TestCliReadNames(unittest.TestCase):
    """
    Directly pin _read_names' stdin-parsing edge behavior, which the happy-path stdin tests
    exercise only incidentally.
    """

    def test_stdin_strips_whitespace_and_drops_blank_lines(self):
        """
        _read_names strips surrounding whitespace from each piped line and drops
        blank/whitespace-only lines, so ragged stdin (indented names, empty
        lines, a trailing newline) still yields exactly the intended names in
        order. Piped through `extract` end-to-end to assert the observable result.
        """
        piped = "  1.0  \n\n\t\nmy_program_v2.0\n   \n"
        with mock.patch.object(cli.sys, "stdin", StdinPipe(piped)):
            exit_code, out, _ = run_cli(["extract"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "1.0\n2.0\n")

    def test_positional_names_take_precedence_over_piped_stdin(self):
        """
        When positional NAMEs are given, _read_names returns them and never
        consults stdin, so piped content is ignored entirely (guards the
        `if names:` early return against a regression that merged both sources).
        """
        with mock.patch.object(cli.sys, "stdin", StdinPipe("PyCharm-9.9.9\n")):
            exit_code, out, _ = run_cli(["extract", "my_program_v1.0"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "1.0\n")


if __name__ == "__main__":
    unittest.main()

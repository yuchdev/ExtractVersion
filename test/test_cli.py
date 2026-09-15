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

    def test_sort_no_input(self):
        with mock.patch.object(cli.sys, "stdin", StdinPipe("")):
            exit_code, out, err = run_cli(["sort"])
        self.assertEqual(exit_code, 2)
        self.assertIn("no input given", err)


class TestCliDirectoryCommands(unittest.TestCase):
    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.cellar_dir = os.path.join(current_dir, "test_data/versions/cellar")
        self.pycharm_dir = os.path.join(current_dir, "test_data/versions/pycharm")

    def test_available_with_path(self):
        exit_code, out, _ = run_cli(["available", "--path", self.cellar_dir, "--json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(out), {"0.01": "0.01", "1.0": "1.0", "0.87": "0.87"})

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


if __name__ == "__main__":
    unittest.main()

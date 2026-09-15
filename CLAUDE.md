# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`extract_version` is a small, dependency-free Python package (published to PyPI as `extract-version`) for
extracting, validating, and sorting version strings embedded in filenames/directory names (e.g. finding
`2020.1.0` in `PyCharm-2020.1.0`, or the latest installed version among a set of directories).

## Commands

Install the package locally (editable, from `src/` layout):
```
pip install -e .
```

Run the full test suite (`unittest`, no pytest config present — CI invokes it directly):
```
python test/test_extract_version.py
```

Run a single test:
```
python -m unittest test.test_extract_version.TestVersionPath.test_sort_versions
```

Run the CLI test suite:
```
python test/test_cli.py
```

Installing the package (editable or otherwise) also registers an `extract-version` console script (equivalently
runnable as `python -m extract_version`), which exposes `extract`, `validate`, `sort`, `available`, and
`last-version` subcommands mirroring the library functions below. Run `extract-version --help` for details.

Lint (matches what CI runs):
```
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

Build/install/uninstall the wheel via the project's release helper (wraps `pip`/`build`):
```
python release_package.py --mode build        # build only
python release_package.py --mode install       # build + install
python release_package.py --mode dev           # build, then `pip install -e .`
python release_package.py --mode reinstall     # uninstall + build + install (default)
python release_package.py --mode uninstall
```
`release_package.py` reads `name`/`version` from `pyproject.toml`'s `[project]` table (via stdlib `tomllib`,
hence the `>=3.11` floor) — nothing about the package name is hardcoded in the script. It also drives releases
end-to-end: `--create-release` tags the repo (`release.<VERSION>`) and creates a GitHub release (wheel only,
via `gh`, requiring release notes for that version to exist first); `--publish-pypi` uploads to PyPI via
`twine` (requires `~/.pypirc`); `--upload-s3` mirrors the built wheel to the shared `packages-s3-useast1-any`
S3 bucket, under a prefix named after the package (`extract-version/`). Bump `version` in `pyproject.toml`
before cutting a release, and add a matching entry to `RELEASE_NOTES.json` under `releases.<VERSION>.release_notes`
(used to generate `RELEASE.md` for the GitHub release body — `sanity_check()` refuses `--create-release` if that
entry is missing).

## Architecture

- **`pyproject.toml`** — single source of truth for both the package version and all packaging metadata
  (PEP 621 `[project]` table; no `setup.py`/`setup.cfg`). `[tool.setuptools.packages.find]` is scoped with
  `include = ["extract_version*"]` — without it, modern setuptools also picks up `src/examples/` as an
  implicit namespace package (it has no `__init__.py`) and ships it in the wheel, which is not intended.
- **`src/extract_version/__init__.py`** — exposes `__version__` by reading it back from installed package
  metadata (`importlib.metadata.version("extract_version")`), so the version still isn't duplicated anywhere
  even though there's no more standalone `version.py`.
- **`src/extract_version/version_info.py`** — all the actual logic, built around two regexes:
  `REG_V1` (`\d+\.\d+\.\d+`, e.g. `1.0.0`) and `REG_V2` (`\d+\.\d+`, e.g. `1.0`), tried in that order (three
  segments before two). Public functions build on each other:
  - `validate_version` — checks a string is *exactly* a version.
  - `extract_version` — finds a version inside an arbitrary string; accepts an optional regex `pattern` with
    one capture group to disambiguate when multiple numeric groups are present (e.g. a version plus an OS
    build number).
  - `available_versions` — maps `{version: original_dir_name}` for a list of names or a directory path.
  - `sort_versions` / `get_last_version` — sort by version tuple (`x.split('.')` cast to ints, so `"10" > "1.0.1"`
    numerically per-component); `get_last_version` composes `available_versions` + `sort_versions`.
- **`src/extract_version/cli.py`** / **`src/extract_version/__main__.py`** — stdlib-`argparse`-only CLI (no new
  dependencies), registered as the `extract-version` console script via `pyproject.toml`'s `[project.scripts]`.
  Each subcommand (`extract`, `validate`, `sort`, `available`, `last-version`) is a thin 1:1 wrapper around the
  matching function in `version_info.py`; commands that take a list of names fall back to reading
  newline-separated entries from stdin when none are given positionally, so they compose in shell pipelines
  (e.g. `ls <dir> | extract-version last-version --pattern '...'`). `--json` switches output from plain text to
  `json.dumps`.
- **`src/examples/`** — runnable scripts (`example_extract_versions.py`, `example_sort_versions.py`,
  `example_available_versions.py`) mirroring the usage examples in `README.md`; keep them in sync if the API
  changes. Not shipped in the built package (see `pyproject.toml` note above).
- **`test/test_extract_version.py`** — tests the library functions, using stdlib `unittest`.
  `test_available_versions` and `test_get_last_version` read real fixture directories under
  `test/test_data/versions/{cellar,pycharm}/` rather than mocking the filesystem — add new fixture dirs there
  when testing directory-scanning behavior.
- **`test/test_cli.py`** — tests `cli.py` by calling `cli.main([...])` directly and capturing stdout/stderr
  (no subprocess), reusing the same `test_data` fixture directories for the `available`/`last-version` cases.
- **`hook/`** — unrelated developer tooling (an IDE spelling-dictionary merge pre-commit hook), not part of
  the published package.

## Notes

- Package layout is `src/`-based (`[tool.setuptools.packages.find] where = ["src"]`), so imports in code and
  tests use `extract_version.version_info`, not a `src.` prefix.
- Requires Python >= 3.11 (per `pyproject.toml`'s `requires-python`) — raised from the previous 3.8 floor
  specifically so `release_package.py` can use stdlib `tomllib` to read `pyproject.toml` without an extra
  dependency. `version_info.py` also uses the walrus operator (`:=`), which just needs 3.8+.
- CI (`.github/workflows/python-app.yml`) runs on Python 3.11 via GitHub Actions on push/PR to `master`, and
  builds+installs the package (`release_package.py --mode install`) before running tests against the
  installed package rather than the source tree.

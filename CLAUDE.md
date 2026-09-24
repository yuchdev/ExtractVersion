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

Run the full test suite with coverage (`pytest` + `pytest-cov`; CI invokes it the same way, gated on the 90%
`fail_under` threshold in `.coveragerc`):
```
pytest --cov=extract_version --cov-report=term-missing
```

The suite is written against stdlib `unittest` (`TestCase` classes), so each file also runs standalone without
pytest, e.g.:
```
python tests/unit/test_version_info.py
python tests/e2e/test_cli.py
```

Run a single test:
```
python -m unittest tests.unit.test_version_info.TestVersionInfoUnit.test_sort_versions
```

Installing the package (editable or otherwise) also registers an `extract-version` console script (equivalently
runnable as `python -m extract_version`), which exposes `extract`, `validate`, `sort`, `available`, and
`last-version` subcommands mirroring the library functions below. Run `extract-version --help` for details.

Lint (matches what CI runs):
```
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

Build/install the wheel via the `release-saga` console script (a separate PyPI package, pinned to
`release-saga>=1.2.0,<2` in `pyproject.toml`'s `dev` dependency group and in CI — that self-installs its own
`build`/`twine` dependencies at runtime). 1.2.0 removed `--mode`: the wheel build always runs first, and
installing is an opt-in pipeline step:
```
release-saga                      # build only
release-saga --local-install      # build + install/upgrade the wheel (uninstalled again if a later step fails)
release-saga --local-dev-mode     # build, then `pip install -e .` (implies --local-install; kept regardless)
pip uninstall extract_version     # uninstall (no release-saga equivalent any more)
release-saga --version            # print [project].version and exit
release-saga --set-version X.Y.Z  # bump pyproject.toml + RELEASE_NOTES.json and exit
release-saga --clean              # roll back the latest interrupted release run and exit
```
`release-saga` reads `name`/`version` from `pyproject.toml`'s `[project]` table, plus optional overrides
from the `[tool.release-saga]` table (this repo sets `s3_bucket = "packages-s3-useast1-any"` and
`git_tag_template = "release.{version}"` there) — nothing about the package name is hardcoded. It also drives
releases end-to-end: `--create-release` tags the repo (`release.<VERSION>`) and creates a GitHub release (wheel
only, via `gh`, requiring release notes for that version to exist first); `--publish-pypi` uploads to PyPI via
`twine` (requires `~/.pypirc`); `--upload-s3` mirrors the built wheel to the shared `packages-s3-useast1-any`
S3 bucket, under a prefix named after the package (`extract-version/`). Bump `version` in `pyproject.toml`
before cutting a release, and add a matching entry to `RELEASE_NOTES.json` under `releases.<VERSION>.release_notes`
(used to generate `RELEASE.md` for the GitHub release body — `release-saga`'s `sanity_check()` refuses
`--create-release` if that entry is missing).

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
- **`tests/`** — organized first by test type, then by the component under test within each type directory
  (`test_version_info.py`, `test_cli.py`, `test_package.py`, matching `src/extract_version/`'s modules). Every
  subdirectory is a package (`__init__.py`) so pytest can tell same-named files (e.g. three `test_cli.py`s)
  apart without an import-path collision. A test's bucket is decided by technique, not by which function it
  calls:
  - **`tests/unit/`** — a single public function, in-memory inputs only (no real filesystem, no CLI, no
    `unittest.mock`).
  - **`tests/integration/`** — multiple internal components collaborating in-memory: either cross-function
    library consistency checks (`extract_version`/`validate_version`/`sort_versions` agreeing with each
    other), or the CLI end-to-end (`cli.main()` → argparse → `version_info.py` → output formatting) via
    plain positional args, still with no real fixture directories and no mocking.
  - **`tests/mock/`** — anything using `unittest.mock`: stdin patched as a pipe or a TTY (`StdinPipe`/
    `StdinTty` in `tests/mock/test_cli.py`) to drive the CLI's stdin-fallback paths, and
    `importlib.metadata.version` patched to exercise `__init__.py`'s `PackageNotFoundError` fallback.
  - **`tests/e2e/`** — real, checked-in fixture directories under `tests/test_data/versions/{cellar,pycharm,
    mixed,filtered,all-invalid,duplicates}/` (`available_versions`/`get_last_version` via `versions_path=` or
    the CLI's `--path`) plus the one test that shells out via `subprocess` to exercise `python -m
    extract_version` for real. Add new fixture dirs under `tests/test_data/versions/` when testing new
    directory-scanning behavior; every e2e file reaches them via `../test_data` since it lives one directory
    below the old flat `tests/`.
- **`tests/test_data/`** — shared fixture directories consumed by `tests/e2e/` (and, for the piped-names
  case, `tests/mock/test_cli.py`).
- **`hook/`** — unrelated developer tooling (an IDE spelling-dictionary merge pre-commit hook), not part of
  the published package.

## Notes

- Package layout is `src/`-based (`[tool.setuptools.packages.find] where = ["src"]`), so imports in code and
  tests use `extract_version.version_info`, not a `src.` prefix.
- Requires Python >= 3.11 (per `pyproject.toml`'s `requires-python`) — raised from the previous 3.8 floor
  when the project's release tooling adopted stdlib `tomllib` to read `pyproject.toml` without an extra
  dependency; the floor is now driven by this project's own packaging/tooling baseline (and `release-saga`
  itself likewise needs 3.11+ for `tomllib`). `version_info.py` also uses the walrus operator (`:=`), which
  just needs 3.8+.
- CI (`.github/workflows/python-app.yml`) runs on Python 3.11 via GitHub Actions on push/PR to `master`,
  installs `release-saga` alongside the other dev tools, and builds+installs the package
  (`release-saga --local-install`) before running tests against the installed package rather than the source tree.
- CI runs the suite via `pytest --cov=extract_version --cov-report=term-missing`, which picks up `.coveragerc`
  automatically; pytest-cov fails the build if coverage drops below the `fail_under = 90` threshold there.

# Extract Version

![license](https://img.shields.io/github/license/yuchdev/ExtractVersion)
![workflow](https://github.com/yuchdev/ExtractVersion/actions/workflows/python-app.yml/badge.svg)
![issues](https://img.shields.io/github/issues/yuchdev/ExtractVersion)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)

Python module for extracting version from the string or directory name. Could make use for creating an
inventory of installed versions of a particular application or finding the latest installed version.

## Table of contents

- [Overview](#overview)
- [Compatibility policy](#compatibility-policy)
- [Dependencies](#dependencies)
- [Setup](#setup)
  - [Install from PyPI](#install-from-pypi)
  - [Install from a release archive](#install-from-a-release-archive)
  - [Install for development](#install-for-development)
- [Usage](#usage)
  - [Library](#library)
  - [Command line](#command-line)
- [Examples](#examples)
  - [Extracting a version from a string](#1-extracting-a-version-from-a-string)
  - [Sorting versioned directories](#2-sorting-versioned-directories)
  - [Disambiguating with a pattern](#3-disambiguating-with-a-pattern)
  - [Building an inventory of installed versions](#4-building-an-inventory-of-installed-versions)
- [Releasing](#releasing)
  - [Release tool prerequisites](#release-tool-prerequisites)
  - [Running a release](#running-a-release)
  - [Rollback behavior](#rollback-behavior)

## Overview

The module offers the following functionality:
* Fetching version string from the string or name of the directory
* Validating version string
* Sorting config and application directories that contain versions in its name

### Supported version shapes

`extract_version` recognizes exactly two version shapes:

| Shape   | Example      | Notes                          |
|---------|--------------|--------------------------------|
| `X.Y`   | `1.0`        | two base-10 integer segments   |
| `X.Y.Z` | `2020.1.0`   | three base-10 integer segments |

The full grammar contract:

* Each segment is a base-10 integer (ASCII digits) separated by literal dots.
  Spaces, signs, and alphabetic suffixes are not allowed, so `v1.0`, `1.0beta`,
  and `1.0.0abc` are rejected. A bare single integer such as `1` or `2020` is
  **not** a version.
* Leading zeros are accepted as input and preserved verbatim in returned
  strings (`1.00` stays `1.00`), while sorting compares each segment
  numerically.
* When a string could match more than one shape, the most specific one wins —
  the three-segment `X.Y.Z` form is preferred over the shorter `X.Y` fragment.
* `extract_version` may match a version embedded in a larger string (e.g.
  `PyCharm-2020.1.0` → `2020.1.0`). An explicit `pattern` (a regex with one
  capture group) is required only to disambiguate when the string contains more
  than one numeric candidate, such as a version plus an OS build number
  (`PyCharm-2018.1.2-windows-10.0`).

## Compatibility policy

Parser hardening keeps the documented happy paths working while tightening a few
behaviors that used to be silently permissive. This section records which is which
so upgrades hold no surprises.

**Preserved for compatibility:**

* All previously valid `X.Y` and `X.Y.Z` inputs still parse, validate, sort, and
  extract to the same results (leading zeros are still accepted and preserved).
* Permissive embedded extraction stays the default. `extract_version` with no
  `pattern` still matches a version embedded anywhere inside a larger name (e.g.
  `PyCharm-2020.1.0` → `2020.1.0`). A `pattern` is required only to disambiguate
  when a name holds more than one numeric candidate (such as a version plus an OS
  build number, `PyCharm-2018.1.2-windows-10.0`) — never for the single-version
  case.
* Duplicate normalized versions resolve deterministically and identically no
  matter where the names came from. When two entries *extract to different but
  normalization-equal* version strings (e.g. `1.0` and `1.0.0`, which both
  normalize to the same numeric key `(1, 0, 0)`, so the string tie-break decides
  the winner), the winner is a pure function of the version strings, so
  `available_versions` / `get_last_version` return the same result whether you
  pass `versions_list=` or `versions_path=`. This does not cover two distinct
  names that extract to the *exact same* string (e.g. `1.0` and `app-1.0` both
  extracting to `1.0`) — there, only one survives in the returned dict, and
  which one is order-dependent rather than covered by this guarantee.

**Intentionally tightened (stricter than before):**

* `validate_version` now requires a full-string match: trailing or leading
  non-version characters are rejected. Migration note: code that relied on
  `validate_version("1.0.0abc")` returning a truthy value now gets `""`.
* `available_versions` no longer surfaces unparseable names under a blank `""`
  key — names whose version cannot be extracted are dropped from the returned
  mapping, so the result contains only valid versions.
* `get_last_version` raises a descriptive `ValueError` when the inventory is
  empty or every entry is unparseable, instead of failing with an opaque error.

## Dependencies

`extract_version` itself is dependency-free at runtime — it only uses the Python standard library, so
`pip install extract-version` pulls in nothing else.

Building, testing, and releasing the project locally pull in a few additional tools, scoped to what you're
doing:

| Purpose            | Tools                              | Needed for                                   |
|--------------------|-------------------------------------|-----------------------------------------------|
| Running tests      | `pytest`, `pytest-cov`             | `tests/{unit,integration,mock,e2e}/`         |
| Building the wheel | `release-saga` (>= 1.2.0, < 2)     | `release-saga`                                |
| Publishing a release | `aws`, `gh`, `twine`              | `release-saga --upload-s3` / `--create-release` / `--publish-pypi` (see [Releasing](#releasing)) |

Requires Python >= 3.11.

## Setup

### Install from PyPI

```
pip install extract-version
```

### Install from a release archive

Archives of previous releases are available on
[GitHub](https://github.com/yuchdev/ExtractVersion/releases), with a mirror on
[AWS](https://packages-s3-useast1-any.s3.dualstack.us-east-1.amazonaws.com/extract-version/extract_version-1.4.0-py3-none-any.whl).

### Install for development

```
pip install -e .
```

This registers the `extract-version` console script against your working copy of `src/extract_version/`, so
edits take effect immediately without reinstalling.

## Usage

### Library

Install the package, then import and call the functions directly — see [Examples](#examples) below for the
functions in action: `extract_version`, `validate_version`, `sort_versions`, `available_versions`, and
`get_last_version`.

### Command line

Installing the package also provides an `extract-version` command (equivalently, `python -m extract_version`)
exposing the same functionality from the shell. Every subcommand also reads its input from stdin when no
arguments are given, so it composes with tools like `ls`/`find`.

```
extract-version extract "PyCharm-2020.1.0"
> 2020.1.0

extract-version extract "PyCharm-2018.1.2-windows-10.0" --pattern "PyCharm-(.*)-windows-10.0"
> 2018.1.2

extract-version sort 2018.1.2 2018.2.0 2020.1.0
> 2018.1.2
> 2018.2.0
> 2020.1.0

ls "C:/Users/user/AppData/Local/JetBrains/PyCharm" | extract-version last-version --pattern "PyCharm-(.*)"
> PyCharm-2020.1.0

extract-version available --path "C:/Users/user/AppData/Local/JetBrains/PyCharm" --json
> {"2018.1.2": "PyCharm-2018.1.2", "2018.2.0": "PyCharm-2018.2.0", "2020.1.0": "PyCharm-2020.1.0"}
```

Run `extract-version --help` or `extract-version <subcommand> --help` for the full option list.

#### Output format

stdout carries only successful results (diagnostics always go to stderr, never
mixed in-band), in one of three shapes:

- **Scalar** — `last-version`, and `sort` when given a single value: the value on
  one line.
- **List** — `extract`, `validate`, and `sort`'s list output: one item per line.
- **Version-to-name mapping** — `available`: one `version<TAB>name` line per
  entry, ordered by the numeric version-sort contract (so `1.9` precedes `1.10`),
  **not** lexicographically by string.

`--json` serializes the same logical content (a JSON scalar, array, or object).
The `available` object's keys appear in the same numeric version order as the
plain-text lines. For partial-success commands (`extract`/`validate`), stdout
holds only the values that succeeded; failed inputs are reported solely on
stderr and never appear in the stdout output.

## Examples

### 1. Extracting a version from a string

We fetch version `2020.1.0` from string `PyCharm-2020.1.0`, or version `1.0` from `my_program_v1.0`.

* `AppVersion.Major.Minor` version format

```python
extract_version(version_string="PyCharm-2020.1.0")
> "2020.1.0"
```

* `Major.Minor` version format

```python
extract_version(version_string="my_program_v1.0")
> "1.0"
```

### 2. Sorting versioned directories

```python
sort_versions(["PyCharm-2018.1.2", "PyCharm-2018.2.0", "PyCharm-2020.1.0"])
> ["PyCharm-2018.1.2", "PyCharm-2018.2.0", "PyCharm-2020.1.0"]
```

### 3. Disambiguating with a pattern

In edge cases with more than one pattern present, e.g. `PyCharm-2018.1.2-windows-10.0`, we should provide a
clue where the version should be extracted from, in a form of a pattern-regex, e.g.
`PyCharm-(.*)-windows-10.0`. The call of such function may look like this:

```python
extract_version(version_string='PyCharm-2018.1.2-windows-10.0', pattern='PyCharm-(.*)-windows-10.0')
> "2018.1.2"
```

#### Pattern error contract

When called with a `pattern`, `extract_version` behaves in one of four ways:

* **No match** — the pattern finds nothing in the string: returns `""` (this is
  "no version found", not a caller error).
* **Wrong capture-group count** — the pattern matches but does not declare
  *exactly one* capture group (zero groups, e.g. a plain or non-capturing
  `(?:...)` pattern, or two or more): raises `PatternArityError` with a message
  like `pattern must contain exactly one capture group`. `PatternArityError` is a
  `ValueError` subclass importable from `extract_version.version_info`, so
  existing `except ValueError` handlers keep catching it, while callers that need
  to single out this case can catch it directly.
* **Invalid regex** — the `pattern` string is not valid regex syntax: Python's
  own `re.error` propagates unchanged (it is not caught or converted).
* **Captured text isn't a version** — the pattern matches with exactly one
  capture group, but the captured text fails version validation: returns `""`.

The CLI (`extract`, `available`, and `last-version` with `--pattern`) catches
both `PatternArityError` and `re.error` and reports them as a friendly stderr
message with exit code 1, rather than surfacing a raw Python traceback.

### 4. Building an inventory of installed versions

```python
application_path = "C:/Users/user/AppData/Local/JetBrains/PyCharm"
pycharm_versions = available_versions(versions_path=application_path)
> {"2018.1.2": "PyCharm-2018.1.2", "2018.2.0": "PyCharm-2018.2.0", "2020.1.0": "PyCharm-2020.1.0"}
```

## Releasing

`release-saga` always builds the wheel first, can install it locally (`--local-install`, or
`--local-dev-mode` for an editable install), and can optionally publish it via `--upload-s3`,
`--create-release` (GitHub), and `--publish-pypi`. Install it first with
`pip install "release-saga>=1.2.0,<2"` — it is a separate PyPI package, not bundled with this project
(it is also listed in the `dev` dependency group in `pyproject.toml`). Version 1.2.0 removed the old
`--mode` flag, so older `release-saga --mode ...` invocations no longer work.

### Release tool prerequisites

Each publishing flag needs its own external tool and credentials, installed and configured beforehand:

| Flag              | Tool     | Credentials                                    |
|-------------------|----------|-------------------------------------------------|
| `--upload-s3`     | `aws`    | `aws configure` (or an `AWS_PROFILE`/instance role) |
| `--create-release`| `gh`     | `gh auth login`                                |
| `--publish-pypi`  | `twine`  | a PyPI API token in `~/.pypirc`                |

Run `python scripts/install_deps.py` to install `aws`, `gh`, and `twine` (cross-platform:
pip-installs `awscli`/`twine` everywhere, and uses Homebrew/winget/apt for `gh` where available).
It does not set up credentials — do that with the commands in the table above.

### Running a release

Run

```
release-saga --create-release --upload-s3 --publish-pypi
```

to perform the full release cycle.

### Rollback behavior

If a tool or its credentials aren't ready when `release-saga` reaches that step, the step
reports itself unavailable and the run rolls back every step already completed (deletes the S3
object, the git tag, and/or the GitHub release, in that order) before exiting — see
`ReleaseStep`/`run_release_pipeline()` in the `release-saga` package.

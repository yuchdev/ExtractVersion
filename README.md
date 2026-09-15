# Extract Version

![license](https://img.shields.io/github/license/yuchdev/ExtractVersion)
![workflow](https://github.com/yuchdev/ExtractVersion/actions/workflows/python-app.yml/badge.svg)
![issues](https://img.shields.io/github/issues/yuchdev/ExtractVersion)

Python module for extracting version from the string or directory name. Could make use for creating an
inventory of installed versions of a particular application or finding the latest installed version.

## Table of contents

- [Overview](#overview)
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

## Dependencies

`extract_version` itself is dependency-free at runtime — it only uses the Python standard library, so
`pip install extract-version` pulls in nothing else.

Building, testing, and releasing the project locally pull in a few additional tools, scoped to what you're
doing:

| Purpose            | Tools                              | Needed for                                   |
|--------------------|-------------------------------------|-----------------------------------------------|
| Running tests      | `pytest`, `pytest-cov`             | `test/test_extract_version.py`, `test/test_cli.py` |
| Building the wheel | `setuptools`, `wheel`, `build`     | `release_package.py --mode build`             |
| Publishing a release | `aws`, `gh`, `twine`              | `release_package.py --upload-s3` / `--create-release` / `--publish-pypi` (see [Releasing](#releasing)) |

Requires Python >= 3.11.

## Setup

### Install from PyPI

```
pip install extract-version
```

### Install from a release archive

Archives of previous releases are available on
[GitHub](https://github.com/yuchdev/ExtractVersion/releases), with a mirror on
[AWS](https://packages-s3-useast1-any.s3.dualstack.us-east-1.amazonaws.com/extract-version/extract_version-1.2.0-py3-none-any.whl).

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

### 4. Building an inventory of installed versions

```python
application_path = "C:/Users/user/AppData/Local/JetBrains/PyCharm"
pycharm_versions = available_versions(versions_path=application_path)
> {"2018.1.2": "PyCharm-2018.1.2", "2018.2.0": "PyCharm-2018.2.0", "2020.1.0": "PyCharm-2020.1.0"}
```

## Releasing

`release_package.py` builds and installs the wheel locally, and can optionally publish it via
`--upload-s3`, `--create-release` (GitHub), and `--publish-pypi`.

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
python release_package.py --mode build --create-release --upload-s3 --publish-pypi
```

to perform the full release cycle.

### Rollback behavior

If a tool or its credentials aren't ready when `release_package.py` reaches that step, the step
reports itself unavailable and the run rolls back every step already completed (deletes the S3
object, the git tag, and/or the GitHub release, in that order) before exiting — see
`ReleaseStep`/`run_release_pipeline()` in `release_package.py`.

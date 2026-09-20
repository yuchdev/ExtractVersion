# Task 02.0 - Library Validation and Extraction

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)

This task translates the version contract into implementable behavior for the
library API in [`src/extract_version/version_info.py`](/src/extract_version/version_info.py).
It is the main specification track for tightening `validate_version()`, sharing
parser logic between public helpers, and documenting how `pattern` capture
should interact with version extraction.

## Subtasks

| Subtask | Focus | Primary files |
|---------|-------|---------------|
| 01 | [Exact `validate_version()`](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/01-exact-validate-version.md) | `src/extract_version/version_info.py`, `test/test_extract_version.py` |
| 02 | [Shared parse helper](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/02-shared-parse-helper.md) | `src/extract_version/version_info.py`, `test/test_extract_version.py` |
| 03 | [Pattern capture rules](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/03-pattern-capture-rules.md) | `src/extract_version/version_info.py`, `test/test_extract_version.py` |
| 04 | [Library tests](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/04-library-tests.md) | `test/test_extract_version.py` |

## Purpose

- Remove ambiguity between what the library says it validates and what it
  actually accepts.
- Prevent duplicated parsing logic from drifting across helper functions.
- Describe the required library tests before implementation begins.

## Target files

- [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- [`test/test_extract_version.py`](/test/test_extract_version.py)
- [`README.md`](/README.md)
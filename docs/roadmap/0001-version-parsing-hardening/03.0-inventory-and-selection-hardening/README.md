# Task 03.0 - Inventory and Selection Hardening

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)

This task defines how inventory helpers should behave when scanning names or
directories that mix valid versions, invalid names, duplicates, and ambiguous
inputs. It governs the selection-facing functions in
[`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
and the filesystem-backed expectations in
[`test/test_extract_version.py`](/test/test_extract_version.py).

## Subtasks

| Subtask | Focus | Primary files |
|---------|-------|---------------|
| 01 | [Invalid-entry filtering](/docs/roadmap/0001-version-parsing-hardening/03.0-inventory-and-selection-hardening/01-invalid-entry-filtering.md) | `src/extract_version/version_info.py`, `test/test_extract_version.py` |
| 02 | [Last-version selection rules](/docs/roadmap/0001-version-parsing-hardening/03.0-inventory-and-selection-hardening/02-last-version-selection-rules.md) | `src/extract_version/version_info.py`, `test/test_extract_version.py` |
| 03 | [Fixtures and tests](/docs/roadmap/0001-version-parsing-hardening/03.0-inventory-and-selection-hardening/03-fixtures-and-tests.md) | `test/test_extract_version.py`, `test/test_data/versions/` |

## Purpose

- Define whether invalid or versionless names are ignored, preserved, or treated
  as errors by inventory helpers.
- Specify stable behavior for duplicates and mixed sources.
- Keep future test fixtures close to real filesystem inputs rather than only
  synthetic unit cases.

## Target files

- [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- [`test/test_extract_version.py`](/test/test_extract_version.py)
- `test/test_data/versions/`
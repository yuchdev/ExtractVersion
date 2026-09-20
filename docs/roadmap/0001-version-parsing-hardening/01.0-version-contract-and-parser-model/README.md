# Task 01.0 - Version Contract and Parser Model

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)

This task defines the authoritative version grammar and normalization model for
Extract Version. Its decisions govern
[`src/extract_version/version_info.py`](/src/extract_version/version_info.py),
the CLI surface in [`src/extract_version/cli.py`](/src/extract_version/cli.py),
and the future expectations recorded in
[`test/test_extract_version.py`](/test/test_extract_version.py) and
[`test/test_cli.py`](/test/test_cli.py).

## Subtasks

| Subtask | Focus | Primary files |
|---------|-------|---------------|
| 01 | [Supported version shapes](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/01-supported-version-shapes.md) | `src/extract_version/version_info.py`, `README.md`, `test/test_extract_version.py` |
| 02 | [Normalized sort key](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/02-normalized-sort-key.md) | `src/extract_version/version_info.py`, `test/test_extract_version.py` |
| 03 | [Compatibility policy](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/03-compatibility-policy.md) | `README.md`, `src/extract_version/version_info.py`, `test/test_extract_version.py`, `test/test_cli.py` |

## Purpose

- Make the supported version grammar explicit instead of letting regex behavior
  define it implicitly.
- Decide how parsed versions are normalized for comparison and sorting.
- Record which current behaviors remain supported and which should tighten in a
  backward-compatible, documented way.

## Target files

- [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- [`README.md`](/README.md)
- [`test/test_extract_version.py`](/test/test_extract_version.py)
- [`test/test_cli.py`](/test/test_cli.py)
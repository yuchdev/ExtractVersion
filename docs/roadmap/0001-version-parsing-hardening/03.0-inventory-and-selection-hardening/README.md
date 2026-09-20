# Task 03.0 - Inventory and Selection Hardening

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)
**Status:** ⬜ Not started
**Depends on:** Tasks 01.0, 02.0

## Scope

This task defines how inventory helpers should behave when scanning names or
directories that mix valid versions, invalid names, duplicates, and ambiguous
inputs. It governs the selection-facing functions in
[`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
and the filesystem-backed expectations in
[`test/test_extract_version.py`](/test/test_extract_version.py).

## Subtasks

| # | Document | Status | Blocks |
|---|----------|--------|--------|
| 01 | [Invalid-entry filtering](01-invalid-entry-filtering.md) | ⬜ Not started | 02, 03 |
| 02 | [Last-version selection rules](02-last-version-selection-rules.md) | ⬜ Not started | 03 |
| 03 | [Fixtures and tests](03-fixtures-and-tests.md) | ⬜ Not started | - |

Subtask 01 depends on Task 02.0's shared parser. Subtask 02 depends on 01;
subtask 03 depends on both 01 and 02.

## Key constraints

- Invalid-entry filtering (Subtask 01) applies identically to `versions_list`
  and `versions_path` inputs - no source-specific special case.
- `get_last_version()` has a documented outcome for every inventory state,
  including "no valid versions remain" - never an incidental `IndexError`.
- Duplicate-normalized-version ties resolve deterministically, independent of
  filesystem or input order.
- Touches: [`src/extract_version/version_info.py`](/src/extract_version/version_info.py),
  [`test/test_extract_version.py`](/test/test_extract_version.py), `test/test_data/versions/`.
</content>

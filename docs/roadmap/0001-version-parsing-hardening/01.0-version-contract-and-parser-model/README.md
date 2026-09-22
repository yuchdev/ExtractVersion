# Task 01.0 - Version Contract and Parser Model

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)
**Status:** ✅ Complete

## Scope

This task defines the authoritative version grammar and normalization model for
Extract Version. Its decisions govern
[`src/extract_version/version_info.py`](/src/extract_version/version_info.py),
the CLI surface in [`src/extract_version/cli.py`](/src/extract_version/cli.py),
and the future expectations recorded in
[`test/test_extract_version.py`](/test/test_extract_version.py) and
[`test/test_cli.py`](/test/test_cli.py).

## Subtasks

| # | Document | Status | Blocks |
|---|----------|--------|--------|
| 01 | [Supported version shapes](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/01-supported-version-shapes.md) | ✅ Complete | 02, 03 |
| 02 | [Normalized sort key](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/02-normalized-sort-key.md) | ✅ Complete | 03 |
| 03 | [Compatibility policy](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/03-compatibility-policy.md) | ✅ Complete | - |

Subtask 01 must land first - it defines the grammar the sort key and
compatibility policy both build on. Subtask 03 depends on both 01 and 02.

## Key constraints

- One canonical grammar and one normalized comparison model - every later
  roadmap task references this task's decisions rather than inventing its own
  parsing or sort rule (contract C1).
- Backward-compatibility effects must be explicit (contract C2): a permissive
  behavior kept for compatibility, and a stricter one, both need a documented
  migration note rather than a silent change.
- Touches: [`src/extract_version/version_info.py`](/src/extract_version/version_info.py),
  [`README.md`](/README.md), [`test/test_extract_version.py`](/test/test_extract_version.py),
  [`test/test_cli.py`](/test/test_cli.py).
</content>

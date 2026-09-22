# Task 02.0 - Library Validation and Extraction

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)
**Status:** ✅ Complete
**Depends on:** Task 01.0

## Scope

This task translates the version contract into implementable behavior for the
library API in [`src/extract_version/version_info.py`](/src/extract_version/version_info.py).
It is the main specification track for tightening `validate_version()`, sharing
parser logic between public helpers, and documenting how `pattern` capture
should interact with version extraction.

## Subtasks

| # | Document | Status | Blocks |
|---|----------|--------|--------|
| 01 | [Exact `validate_version()`](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/01-exact-validate-version.md) | ✅ Complete | 02 |
| 02 | [Shared parse helper](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/02-shared-parse-helper.md) | ✅ Complete | 03, 04 |
| 03 | [Pattern capture rules](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/03-pattern-capture-rules.md) | ✅ Complete | 04 |
| 04 | [Library tests](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/04-library-tests.md) | ✅ Complete | - |

Subtask 01 depends on Task 01.0's grammar. Subtask 02 depends on 01; subtask
03 depends on 02; subtask 04 depends on all of 01-03.

## Key constraints

- Every public entry point (`validate_version`, `extract_version`,
  `sort_versions`, `available_versions`, `get_last_version`) routes through the
  one shared internal parse helper from Subtask 02 - no duplicated regex or
  `split('.')` logic (contract C1).
- The shared parse helper stays private; hardening improves consistency
  without expanding the documented top-level API surface.
- Pattern-based extraction routes captured values through the same exact
  validator as non-pattern extraction - no bypass path.
- Touches: [`src/extract_version/version_info.py`](/src/extract_version/version_info.py),
  [`test/test_extract_version.py`](/test/test_extract_version.py).
</content>

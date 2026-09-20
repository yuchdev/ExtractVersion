# Subtask 02 - Shared Parse Helper

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)
**Parent task:** [`02.0-library-validation-and-extraction/README.md`](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/README.md)

## Objective

Consolidate version parsing into one internal helper so validation, extraction,
sorting, inventory, and selection stop drifting apart.

## Affected files

- [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- [`test/test_extract_version.py`](/test/test_extract_version.py)

## Required behavior

- Introduce one private parsing entry point in
  [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
  that can validate a standalone candidate and normalize it for comparison.
- Reuse that helper from `validate_version()` and `extract_version()` first, and
  structure it so `sort_versions()`, `available_versions()`, and
  `get_last_version()` can consume the same parse result rather than rebuilding
  their own heuristics.
- Keep the helper's output rich enough to avoid reparsing, for example by
  carrying both the original matched string and a normalized numeric form.
- Avoid exposing the helper as new public API; hardening should improve
  consistency without expanding the documented top-level surface.

## Tests to add or update later

- Indirectly verify the helper through public functions that now share behavior.
- Add mixed-function regression cases proving that the same candidate accepted by
  `extract_version()` also validates and sorts consistently.

## Success criteria

- Parser logic exists in one internal place instead of being duplicated across
  regex matches and ad hoc `split('.')` conversions.
- Future changes to version grammar require updating one helper and its shared
  tests rather than several loosely related functions.
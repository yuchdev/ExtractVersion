# 04 - Library Tests

**Parent task:** [`02.0-library-validation-and-extraction/README.md`](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/README.md)
**State:** ⬜ Not started
**Depends on:** 01, 02, 03
**Blocks:** -

## Objective

Refresh the library test suite so the parser hardening work is locked down by
behavioral coverage before and after implementation.

## Files

- **Modify** [`test/test_extract_version.py`](/test/test_extract_version.py)
- **Modify** [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)

## Required behavior

- Reorganize or extend the existing test cases so exact validation, extraction,
  and sorting each have both happy-path and contract-edge coverage.
- Add targeted regression tests for the current roadmap gaps:
  exact-match validation, single-component support if adopted, consistent
  pattern capture handling, and stable numeric sorting.
- Keep tests focused on public functions instead of asserting on private helper
  internals.
- Preserve the current `unittest` style and direct imports used by the existing
  suite.

## Tests to add or update later

- Extend `test_validate_version_invalid` with exact-match negatives.
- Add extraction cases that prove pattern and non-pattern code paths share the
  same parser behavior.
- Add sort cases that exercise every supported version shape and the chosen tie
  policy.

## Success criteria

- [ ] `test/test_extract_version.py` becomes the authoritative regression suite
      for parser behavior.
- [ ] Future parser changes fail fast when they reintroduce prefix matching,
      sorting drift, or inconsistent extraction rules.
</content>

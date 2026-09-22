# 01 - Exact `validate_version()`

**Parent task:** [`02.0-library-validation-and-extraction/README.md`](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/README.md)
**State:** ⬜ Not started
**Depends on:** Task 01.0
**Blocks:** 02

## Objective

Make `validate_version()` enforce the exact parser contract instead of accepting
strings that only begin with a valid-looking version.

## Files

- **Modify** [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- **Modify** [`test/test_extract_version.py`](/test/test_extract_version.py)

## Required behavior

- Replace the current prefix-based acceptance (`re.match`) with exact
  whole-string validation that reuses the canonical parser contract from Task
  `01.0`.
- Continue returning the original input string for valid versions and `""` for
  invalid inputs so the public return type remains unchanged.
- Reject strings that contain extra prefix/suffix content, such as `v1.0`,
  `1.0beta`, `1.0.0-linux`, or any other shape not explicitly allowed by Task
  `01.0`.
- Ensure the exact validation logic stays consistent with the strings that
  `extract_version()` may return.

## Tests to add or update later

- Expand [`test/test_extract_version.py`](/test/test_extract_version.py) with
  exact-match negatives, not just obviously malformed strings like `0.`.
- Add CLI coverage in [`test/test_cli.py`](/test/test_cli.py) for `validate`
  rejecting strings that previously passed accidentally.

## Success criteria

- [ ] `validate_version()` no longer accepts a valid prefix followed by junk.
- [ ] The function's docstring, implementation, and tests all agree on “exact
      version” semantics.
</content>

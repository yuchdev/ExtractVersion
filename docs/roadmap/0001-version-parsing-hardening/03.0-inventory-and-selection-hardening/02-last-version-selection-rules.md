# 02 - Last-Version Selection Rules

**Parent task:** [`03.0-inventory-and-selection-hardening/README.md`](/docs/roadmap/0001-version-parsing-hardening/03.0-inventory-and-selection-hardening/README.md)
**State:** ⬜ Not started
**Depends on:** 01
**Blocks:** 03

## Objective

Specify deterministic rules for `get_last_version()` once invalid entries and
duplicate normalized versions are possible inputs.

## Files

- **Modify** [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- **Modify** [`test/test_extract_version.py`](/test/test_extract_version.py)

## Required behavior

- Base `get_last_version()` on the filtered, normalized inventory contract from
  Task `03.0` Subtask `01` instead of relying on whatever keys happen to appear
  in a raw dict comprehension.
- Define the library behavior when no valid versions remain after filtering; this
  milestone should prefer a deliberate exception or other documented outcome over
  the current accidental `IndexError` path.
- Keep the existing precedence rule where `versions_path` wins over
  `versions_list`, and document it explicitly in tests.
- Choose a deterministic winner when two names normalize to the same newest
  version, so filesystem ordering does not silently change the result.

## Tests to add or update later

- Add empty-after-filtering coverage for `get_last_version()`.
- Add duplicate-version cases from both list input and directory-backed input.
- Preserve the existing fixture-based happy-path checks.

## Success criteria

- [ ] `get_last_version()` returns a documented result or failure mode for every
      inventory state.
- [ ] The newest-version choice is stable across repeated runs and input sources.
</content>

# 03 - Fixtures and Tests

**Parent task:** [`03.0-inventory-and-selection-hardening/README.md`](/docs/roadmap/0001-version-parsing-hardening/03.0-inventory-and-selection-hardening/README.md)
**State:** ⬜ Not started
**Depends on:** 01, 02
**Blocks:** -

## Objective

Expand fixture-backed coverage so inventory and selection hardening is exercised
against realistic directory inputs, not only synthetic lists.

## Files

- **Modify** [`test/test_extract_version.py`](/test/test_extract_version.py)
- **Modify** `test/test_data/versions/`

## Required behavior

- Add one or more dedicated fixture directories under `test/test_data/versions/`
  for mixed valid/invalid entries, duplicates, and any new supported version
  shapes that affect inventory behavior.
- Keep fixture names readable enough that failures explain themselves when the
  tests compare expected maps and last-version results.
- Reuse those fixtures from both library and CLI tests where appropriate instead
  of duplicating ad hoc inline name lists everywhere.

## Tests to add or update later

- Extend [`test/test_extract_version.py`](/test/test_extract_version.py) with
  fixture-backed assertions for `available_versions()` and `get_last_version()`.
- Mirror key fixture cases in [`test/test_cli.py`](/test/test_cli.py) for
  `available --path` and `last-version --path`.

## Success criteria

- [ ] Inventory behavior is validated against real directories, matching how the
      package is used in practice.
- [ ] Future regressions in invalid-entry filtering or duplicate handling can be
      reproduced from stable fixture data.
</content>

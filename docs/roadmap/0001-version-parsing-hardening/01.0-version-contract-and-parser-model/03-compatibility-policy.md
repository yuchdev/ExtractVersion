# 03 - Compatibility Policy

**Parent task:** [`01.0-version-contract-and-parser-model/README.md`](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/README.md)
**State:** ⬜ Not started
**Depends on:** 01, 02
**Blocks:** -

## Objective

Record which current behaviors are preserved for compatibility and which ones are
intentionally tightened as part of parser hardening.

## Files

- **Modify** [`README.md`](/README.md)
- **Modify** [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- **Modify** [`test/test_extract_version.py`](/test/test_extract_version.py)
- **Modify** [`test/test_cli.py`](/test/test_cli.py)

## Required behavior

- Keep all existing documented happy paths that remain within the new parser
  contract, including the currently tested `X.Y` and `X.Y.Z` cases.
- Call out behavior changes that should become stricter, especially exact
  validation and the removal of empty-string inventory keys.
- State whether permissive extraction from larger names remains supported by
  default, and which ambiguous cases must move behind `--pattern` / `pattern=`.
- Define the compatibility stance for duplicate normalized versions, including
  whether the winning original name is stable across list and path inputs.
- Require README and CLI help text updates wherever the old wording would imply
  a looser or different contract than the implementation will enforce.

## Tests to add or update later

- Preserve current passing cases that remain valid under the new contract.
- Add regression coverage for every intentional tightening so the change is
  explicit rather than discovered accidentally.

## Success criteria

- [ ] Contributors can tell which behavior shifts are deliberate and user-visible.
- [ ] Later implementation work has a documented boundary between compatibility
      preservation and planned breaking-style corrections.
</content>

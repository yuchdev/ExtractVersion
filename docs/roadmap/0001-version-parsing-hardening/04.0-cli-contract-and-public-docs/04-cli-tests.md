# 04 - CLI Tests

**Parent task:** [`04.0-cli-contract-and-public-docs/README.md`](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/README.md)
**State:** ⬜ Not started
**Depends on:** 01, 02, 03
**Blocks:** -

## Objective

Extend the CLI test suite so the hardened user-facing contract is regression-
tested independently of the library unit tests.

## Files

- **Modify** [`test/test_cli.py`](/test/test_cli.py)
- **Modify** [`src/extract_version/cli.py`](/src/extract_version/cli.py)

## Required behavior

- Keep testing the CLI by calling `cli.main([...])` directly and capturing
  stdout/stderr, matching the existing suite style.
- Add command coverage for exact validation failures, pattern-capture edge
  cases, mixed valid/invalid inventory inputs, and no-version-found cases for
  `last-version`.
- Assert both output content and exit code so user-visible behavior changes are
  intentional.
- Reuse fixture directories from `test/test_data/versions/` when path-based CLI
  behavior matters.

## Tests to add or update later

- Add `--json` checks for each command family where output structure matters.
- Add path-vs-stdin precedence coverage for `available` and `last-version`.
- Add regression cases for stderr-only failures versus mixed stdout/stderr runs.

## Success criteria

- [ ] `test/test_cli.py` becomes the contract suite for command-line behavior.
- [ ] CLI changes that would surprise shell users are caught before release.
</content>

# 01 - CLI Error Contract

**Parent task:** [`04.0-cli-contract-and-public-docs/README.md`](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/README.md)
**State:** ⬜ Not started
**Depends on:** Task 03.0
**Blocks:** 02, 04

## Objective

Make the command-line interface's exit-code and stderr behavior explicit so users
and tests can distinguish invalid input, missing input, and partial success.

## Files

- **Modify** [`src/extract_version/cli.py`](/src/extract_version/cli.py)
- **Modify** [`test/test_cli.py`](/test/test_cli.py)

## Required behavior

- Document the exit-code contract already implied by the current CLI structure:
  `0` for full success, `1` for semantic failure or partial failure, and `2` for
  missing input / argument-usage problems.
- Specify command-by-command stderr messaging for `extract`, `validate`, `sort`,
  `available`, and `last-version`.
- Keep JSON/plain-text success output on stdout and error diagnostics on stderr.
- Define whether commands that process multiple names should emit successful
  results alongside failures (as `extract` currently does) or move to all-or-
  nothing behavior; whichever direction is chosen must be reflected in tests.

## Tests to add or update later

- Add explicit assertions for exit codes and stderr content in
  [`test/test_cli.py`](/test/test_cli.py) across every subcommand.
- Add coverage for “no valid version found” after inventory filtering so
  `last-version` no longer relies on catching incidental exceptions only.

## Success criteria

- [ ] Every subcommand has a written, testable error contract.
- [ ] CLI callers can rely on consistent exit codes and stderr routing.
</content>

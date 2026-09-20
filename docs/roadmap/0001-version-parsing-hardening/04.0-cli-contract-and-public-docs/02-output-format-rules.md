# 02 - Output Format Rules

**Parent task:** [`04.0-cli-contract-and-public-docs/README.md`](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/README.md)
**State:** ⬜ Not started
**Depends on:** 01
**Blocks:** 03, 04

## Objective

Define stable stdout formats for plain-text and `--json` output so CLI consumers
are insulated from parser and inventory hardening changes.

## Files

- **Modify** [`src/extract_version/cli.py`](/src/extract_version/cli.py)
- **Modify** [`test/test_cli.py`](/test/test_cli.py)
- **Modify** [`README.md`](/README.md)

## Required behavior

- Document the shape of plain-text output for scalars, lists, and version-to-name
  mappings.
- Decide whether mapping output should be ordered lexicographically by string key
  or by the normalized version sort contract from Task `01.0`; the roadmap
  should favor one explicit ordering rule.
- Ensure `--json` outputs serialize the same logical content as plain-text mode
  without mixing diagnostics into stdout.
- Clarify whether partial-success commands include only successful values in
  stdout or also represent failed inputs in-band.

## Tests to add or update later

- Add CLI assertions for plain-text and JSON output ordering.
- Add mixed-success cases for `extract` and `validate` so output shape remains
  predictable when stderr also contains errors.

## Success criteria

- [ ] CLI output is specified as a contract, not inferred from `print()` behavior.
- [ ] README examples, CLI tests, and actual command output all align on one
      format.
</content>

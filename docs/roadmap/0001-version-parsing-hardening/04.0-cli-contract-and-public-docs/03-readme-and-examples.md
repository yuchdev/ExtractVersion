# Subtask 03 - README and Examples

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)
**Parent task:** [`04.0-cli-contract-and-public-docs/README.md`](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/README.md)

## Objective

Bring the public documentation and example scripts into line with the hardened
parser and CLI contract.

## Affected files

- [`README.md`](/README.md)
- `src/examples/`
- [`test/test_cli.py`](/test/test_cli.py)

## Required behavior

- Update README examples so they show only supported version shapes and the final
  pattern-capture expectations.
- Refresh command-line examples to match the agreed stdout/stderr and exit-code
  contract.
- Keep runnable example scripts under `src/examples/` aligned with the same
  public behavior described in the README.
- Remove or rewrite any wording that suggests looser validation or extraction
  semantics than the hardened library actually supports.

## Tests to add or update later

- Verify example-driven CLI cases in [`test/test_cli.py`](/test/test_cli.py)
  where that provides useful coverage.
- Manually re-run the documented commands once the implementation lands.

## Success criteria

- Public docs no longer contradict the real parser and CLI behavior.
- README and examples can be used as reliable onboarding material for the
  hardened contract.
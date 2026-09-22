# Task 04.0 - CLI Contract and Public Docs

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)
**Status:** ✅ Complete
**Depends on:** Tasks 01.0, 02.0, 03.0

## Scope

This task defines the user-facing contract for the command-line interface and
the public documentation that describes it. It covers
[`src/extract_version/cli.py`](/src/extract_version/cli.py),
[`README.md`](/README.md), and the command-line expectations in
[`test/test_cli.py`](/test/test_cli.py).

## Subtasks

| # | Document | Status | Blocks |
|---|----------|--------|--------|
| 01 | [CLI error contract](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/01-cli-error-contract.md) | ✅ Complete | 02, 04 |
| 02 | [Output format rules](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/02-output-format-rules.md) | ✅ Complete | 03, 04 |
| 03 | [README and examples](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/03-readme-and-examples.md) | ✅ Complete | 04 |
| 04 | [CLI tests](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/04-cli-tests.md) | ✅ Complete | - |

Subtask 01 depends on Task 03.0's inventory contract. Subtask 02 depends on
01; subtask 03 depends on 02; subtask 04 depends on all of 01-03.

## Key constraints

- Exit codes stay `0` (success) / `1` (semantic or partial failure) / `2`
  (usage error); JSON/plain-text output stays on stdout, diagnostics on
  stderr (contract C3).
- CLI output ordering and pattern-capture edge cases match the Task
  01.0/02.0 contracts exactly - no separate CLI-only parsing rule.
- `README.md` and `src/examples/` never describe looser validation or
  extraction semantics than the hardened library enforces.
- Touches: [`src/extract_version/cli.py`](/src/extract_version/cli.py),
  [`README.md`](/README.md), `src/examples/`, [`test/test_cli.py`](/test/test_cli.py).
</content>

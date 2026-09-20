# Task 04.0 - CLI Contract and Public Docs

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)

This task defines the user-facing contract for the command-line interface and
the public documentation that describes it. It covers
[`src/extract_version/cli.py`](/src/extract_version/cli.py),
[`README.md`](/README.md), and the command-line expectations in
[`test/test_cli.py`](/test/test_cli.py).

## Subtasks

| Subtask | Focus | Primary files |
|---------|-------|---------------|
| 01 | [CLI error contract](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/01-cli-error-contract.md) | `src/extract_version/cli.py`, `test/test_cli.py` |
| 02 | [Output format rules](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/02-output-format-rules.md) | `src/extract_version/cli.py`, `test/test_cli.py`, `README.md` |
| 03 | [README and examples](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/03-readme-and-examples.md) | `README.md`, `src/examples/`, `test/test_cli.py` |
| 04 | [CLI tests](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/04-cli-tests.md) | `test/test_cli.py` |

## Purpose

- Standardize stdout, stderr, exit behavior, and JSON/plain-text responses.
- Keep public examples aligned with the eventual library contract.
- Describe the CLI regression coverage needed once implementation starts.

## Target files

- [`src/extract_version/cli.py`](/src/extract_version/cli.py)
- [`README.md`](/README.md)
- `src/examples/`
- [`test/test_cli.py`](/test/test_cli.py)
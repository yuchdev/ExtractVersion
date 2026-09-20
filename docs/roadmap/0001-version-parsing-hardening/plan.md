# Milestone 0001 - Version Parsing and Selection Hardening

**Package:** `extract-version` | **Module root:** `src/extract_version/`
**Depends on:** Existing library and CLI contract in `version_info.py`, `cli.py`, and `test/`

This milestone is the first real roadmap slice for Extract Version. It hardens
the package's core value path in
[`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
and the thin CLI wrapper in [`src/extract_version/cli.py`](/src/extract_version/cli.py)
by turning the current implicit behavior into a documented, implementable
contract for version parsing, validation, inventory, and selection.

Today the code exposes several roadmap-worthy gaps: `validate_version()` claims
an exact check but only start-matches; `extract_version()` documents support for
single-component versions without implementing that contract; inventory helpers
can retain invalid or empty-version entries; and CLI output/error behavior is
not yet normalized across success and failure cases.

## Table of contents

- [Tasks](#tasks)
- [Milestone scope and contracts](#milestone-scope-and-contracts)
- [Dependency notes](#dependency-notes)
- [Per-task specifications](#per-task-specifications)

---

## Tasks

| Task | Name | Category | Output |
|------|------|----------|--------|
| 01.0 | Version Contract and Parser Model | contract | Canonical version grammar, normalization, and compatibility rules |
| 02.0 | Library Validation and Extraction | library | Implementable spec for exact validation, shared parsing, and extraction behavior |
| 03.0 | Inventory and Selection Hardening | library | Implementable spec for `available_versions()` / `get_last_version()` on mixed inputs |
| 04.0 | CLI Contract and Public Docs | cli/docs | CLI behavior contract plus README/examples/test alignment |

Tasks `01.0` → `04.0` are intentionally sequential. The parser contract must be
settled before library changes are specified; inventory/selection rules should
reuse that parser contract; and CLI/public docs should be updated only after the
library-facing behavior is fully defined.

---

## Milestone scope and contracts

### In scope

- Define one canonical version contract shared by validation, extraction,
  sorting, inventory, and CLI output.
- Specify future changes against concrete files:
  [`src/extract_version/version_info.py`](/src/extract_version/version_info.py),
  [`src/extract_version/cli.py`](/src/extract_version/cli.py),
  [`README.md`](/README.md),
  [`test/test_extract_version.py`](/test/test_extract_version.py), and
  [`test/test_cli.py`](/test/test_cli.py).
- Keep every task and subtask small enough to be implemented as a later,
  reviewable code change rather than a whole-milestone rewrite.

### Out of scope

- Shipping the implementation described here in `src/extract_version/`.
- Changing release tooling, packaging metadata, or unrelated documentation.

### Shared milestone contracts (authoritative)

#### C1 - One canonical parser contract

The milestone standardizes around one parser model for all public entry points.
`validate_version()`, `extract_version()`, `sort_versions()`,
`available_versions()`, and `get_last_version()` must eventually agree on what
counts as a valid version and how it is normalized for comparison.

#### C2 - Compatibility must be explicit

Where the future implementation keeps permissive behavior for backward
compatibility, the roadmap docs must say so directly. Where behavior becomes
stricter (for example, exact validation or filtering invalid inventory entries),
the corresponding task must call out the migration effect in tests and docs.

#### C3 - CLI is a contract surface, not just a wrapper

Although [`src/extract_version/cli.py`](/src/extract_version/cli.py) is thin, it
defines user-visible exit codes, stdout/stderr routing, and JSON/plain-text
output behavior. Those expectations need milestone-level treatment rather than
being left as incidental side effects of the library internals.

---

## Dependency notes

- **Task 01.0** establishes the supported version shapes and normalized sort
  model that every later task depends on.
- **Task 02.0** translates that contract into exact library behavior for
  validation and extraction in `version_info.py`.
- **Task 03.0** depends on Tasks `01.0` and `02.0` because inventory and
  last-version selection should build on the same parse result rather than a
  second, inconsistent heuristic.
- **Task 04.0** depends on Tasks `01.0` through `03.0` because CLI messaging,
  README examples, and CLI tests must reflect the final library contract.

---

## Per-task specifications

- [`01.0-version-contract-and-parser-model/README.md`](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/README.md)
- [`02.0-library-validation-and-extraction/README.md`](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/README.md)
- [`03.0-inventory-and-selection-hardening/README.md`](/docs/roadmap/0001-version-parsing-hardening/03.0-inventory-and-selection-hardening/README.md)
- [`04.0-cli-contract-and-public-docs/README.md`](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/README.md)
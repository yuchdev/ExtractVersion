# Milestone 0001 - Version Parsing and Selection Hardening - Status

Tracks progress against [plan.md](/docs/roadmap/0001-version-parsing-hardening/plan.md).
Updated as each task lands.

## Current status

| Task | Name                               | Status         | Notes |
|------|-------------------------------------|----------------|-------|
| 01.0 | Version Contract and Parser Model  | ⬜ Not started | Waiting for implementation work to define the authoritative parser contract. |
| 02.0 | Library Validation and Extraction  | ⬜ Not started | Follows the contract decisions from Task 01.0. |
| 03.0 | Inventory and Selection Hardening  | ⬜ Not started | Depends on the shared parser behavior from Tasks 01.0 and 02.0. |
| 04.0 | CLI Contract and Public Docs        | ⬜ Not started | Should be implemented after the library-facing contract is settled. |

**Legend:** ✅ Complete · 🔶 In progress / partial · ⬜ Not started

**Current gate status:** No tasks started. This is a **planning-only milestone**
- every document under this tree specifies a future contract or test change; no
product code in `src/extract_version/` has shipped from it yet. Tasks are
strictly sequential (`01.0 → 02.0 → 03.0 → 04.0`); see
[plan.md § Dependency notes](/docs/roadmap/0001-version-parsing-hardening/plan.md#dependency-notes).

## Notes & decisions

- **Planning-only scope.** No product code changes ship as part of the roadmap
  documentation itself; each subtask becomes a reviewable code change once
  implementation begins.
- **Strict sequencing.** The parser contract (01.0) must be settled before
  library behavior is specified (02.0); inventory/selection (03.0) reuses that
  parser contract; CLI/public docs (04.0) update only after the library-facing
  contract is final. Tasks do not proceed in parallel.
- **Update discipline.** Progress should be recorded here - with the icon
  legend above - as soon as implementation work begins on any task or subtask.

## Decomposition tree (as planned)

The milestone is decomposed into **4 tasks / 14 subtasks** (20 Markdown files
total, including `plan.md` and this `status.md`).

```
docs/roadmap/0001-version-parsing-hardening/
├── plan.md                                        ← milestone spec (## Tasks, contracts C1–C3)
├── status.md                                      ← this tracker
├── 01.0-version-contract-and-parser-model/        ← contract
│   ├── README.md
│   ├── 01-supported-version-shapes.md
│   ├── 02-normalized-sort-key.md
│   └── 03-compatibility-policy.md
├── 02.0-library-validation-and-extraction/        ← library
│   ├── README.md
│   ├── 01-exact-validate-version.md
│   ├── 02-shared-parse-helper.md
│   ├── 03-pattern-capture-rules.md
│   └── 04-library-tests.md
├── 03.0-inventory-and-selection-hardening/        ← library
│   ├── README.md
│   ├── 01-invalid-entry-filtering.md
│   ├── 02-last-version-selection-rules.md
│   └── 03-fixtures-and-tests.md
└── 04.0-cli-contract-and-public-docs/             ← cli/docs
    ├── README.md
    ├── 01-cli-error-contract.md
    ├── 02-output-format-rules.md
    ├── 03-readme-and-examples.md
    └── 04-cli-tests.md
```

## Per-task detail

_Filled in as tasks complete (Delivered list + test coverage summary per task,
once implementation begins)._

### Task 01.0 - Version Contract and Parser Model (⬜ Not started)

Not started. See [`01.0-version-contract-and-parser-model/README.md`](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/README.md)
for scope.

### Task 02.0 - Library Validation and Extraction (⬜ Not started)

Not started. Depends on Task 01.0. See [`02.0-library-validation-and-extraction/README.md`](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/README.md)
for scope.

### Task 03.0 - Inventory and Selection Hardening (⬜ Not started)

Not started. Depends on Tasks 01.0 and 02.0. See [`03.0-inventory-and-selection-hardening/README.md`](/docs/roadmap/0001-version-parsing-hardening/03.0-inventory-and-selection-hardening/README.md)
for scope.

### Task 04.0 - CLI Contract and Public Docs (⬜ Not started)

Not started. Depends on Tasks 01.0-03.0. See [`04.0-cli-contract-and-public-docs/README.md`](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/README.md)
for scope.
</content>

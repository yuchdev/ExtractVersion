---
sessionId: session-260921-030423-1h0z
---

# Requirements

### Overview & Goals
Add the first real milestone under `docs/roadmap/` and use it to propose a concrete product improvement for ExtractVersion: **structured version parsing and selection hardening**.

The roadmap docs should mirror the shape already defined in `docs/roadmap/README.md` and the AegisSwr example: one milestone folder with `plan.md` and `status.md`, task folders with `README.md`, and per-subtask spec files.

### Scope
#### In Scope
- Create one milestone in `docs/roadmap/` describing a high-value improvement to the package.
- Split that milestone into several tasks, and each task into actionable subtasks.
- Update `docs/roadmap/README.md` so its milestone index reflects files that actually exist.
- Add or repair supporting roadmap context so local roadmap links are valid.

#### Out of Scope
- Implementing the milestone’s product changes in `src/extract_version/`.
- Changing package behavior, tests, or release tooling beyond documenting future work.

### Why this milestone
The repository’s core value is concentrated in `src/extract_version/version_info.py`, with `src/extract_version/cli.py` acting as a thin wrapper. That core currently has clear roadmap-worthy gaps:
- `validate_version()` claims exact validation but only start-matches.
- `extract_version()` only handles `X.Y.Z` / `X.Y`, while its own docstring mentions `1`.
- `available_versions()` can include empty-string keys for names with no version.
- CLI error handling in `cli.py` is only partially normalized.

### Deliverable
A roadmap slice that a contributor can pick up and implement incrementally, with every task/subtask pointing at concrete repo files such as `src/extract_version/version_info.py`, `src/extract_version/cli.py`, `README.md`, `test/test_extract_version.py`, and `test/test_cli.py`.

# Technical Design

### Current Implementation
- `src/extract_version/version_info.py` contains all public library behavior: `validate_version`, `extract_version`, `sort_versions`, `available_versions`, and `get_last_version`.
- `src/extract_version/cli.py` is a thin `argparse` layer over those functions.
- `test/test_extract_version.py` and `test/test_cli.py` define the current library and CLI contract.
- `docs/roadmap/README.md` already defines the `Milestone → Task → Subtask` structure, but there are no actual milestone folders under `docs/roadmap/`.
- The current roadmap index references milestone files that do not exist, so the roadmap docs need self-consistency cleanup as part of this work.

### Key Decisions
- Use **`0001`** for the new milestone, because there are no real milestone directories yet and the current roadmap file is functioning as a scaffold.
- Center the milestone on **version parsing and selection hardening**, since that is the package’s core domain and the clearest gap in the current implementation.
- Follow the AegisSwr structure closely: milestone `plan.md`/`status.md`, task `README.md`, subtask `NN-*.md` specs.
- Repair roadmap self-links by updating `docs/roadmap/README.md` and adding a minimal `docs/roadmap/roadmap.md` overview instead of leaving dangling references.

### Proposed Milestone
#### Milestone folder
- `docs/roadmap/0001-version-parsing-hardening/plan.md`
- `docs/roadmap/0001-version-parsing-hardening/status.md`

#### Planned tasks
1. `01.0-version-contract-and-parser-model`
   - Define supported version shapes and normalization rules.
   - Align extraction, validation, and sorting around one canonical contract.
2. `02.0-library-validation-and-extraction`
   - Specify the implementation work for exact validation, shared parsing, and pattern handling in `src/extract_version/version_info.py`.
3. `03.0-inventory-and-selection-hardening`
   - Cover `available_versions()` / `get_last_version()` behavior for invalid names, duplicates, and mixed inputs.
4. `04.0-cli-contract-and-public-docs`
   - Define the CLI-side contract in `src/extract_version/cli.py`, plus updates to `README.md`, examples, and CLI tests.

### Planned subtask shape
Each task folder will contain a `README.md` plus focused subtask specs such as:
- Task `01.0`: supported-version grammar, normalized sort key, compatibility policy.
- Task `02.0`: exact `validate_version`, shared parser helper, pattern-capture rules, library tests.
- Task `03.0`: invalid-entry filtering, last-version selection rules, fixture/test coverage.
- Task `04.0`: CLI exit/error contract, JSON/stdout-stderr rules, README/example refresh, CLI tests.

### File Structure
```text
docs/roadmap/
  README.md
  roadmap.md
  0001-version-parsing-hardening/
    plan.md
    status.md
    01.0-version-contract-and-parser-model/
      README.md
      01-supported-version-shapes.md
      02-normalized-sort-key.md
      03-compatibility-policy.md
    02.0-library-validation-and-extraction/
      README.md
      01-exact-validate-version.md
      02-shared-parse-helper.md
      03-pattern-capture-rules.md
      04-library-tests.md
    03.0-inventory-and-selection-hardening/
      README.md
      01-invalid-entry-filtering.md
      02-last-version-selection-rules.md
      03-fixtures-and-tests.md
    04.0-cli-contract-and-public-docs/
      README.md
      01-cli-error-contract.md
      02-output-format-rules.md
      03-readme-and-examples.md
      04-cli-tests.md
```

### Risks
- If the milestone promises too many new version formats at once, the roadmap will become vague instead of actionable.
- If `docs/roadmap/README.md` is not reconciled with actual files, the new roadmap docs will ship with broken internal links.
- If subtasks are too broad, they will not be usable as implementation-sized specs; each subtask should stay close to one logical code/test/doc slice.

# Testing

### Validation Approach
- Verify the roadmap hierarchy matches the local convention in `docs/roadmap/README.md`:
  - milestone folder with `plan.md` and `status.md`
  - task folders with `README.md`
  - subtask files named `NN-*.md`
- Run `python scripts/check_doc_links.py docs/` to ensure every new roadmap link resolves.
- Confirm every roadmap spec references real repository targets such as `src/extract_version/version_info.py`, `src/extract_version/cli.py`, `README.md`, `test/test_extract_version.py`, and `test/test_cli.py`.

### Key Scenarios
- `docs/roadmap/README.md` links to the new milestone and only to files that exist.
- `docs/roadmap/0001-version-parsing-hardening/plan.md` contains a task table and dependency notes consistent with the task folders created.
- Every task `README.md` links to real subtask files.
- Every subtask document contains enough detail to guide a later implementation pass.

### Test Changes
- No product-code tests are required for this docs-only change.
- Validation is documentation-focused: structure, links, and alignment with the existing package files.

# Delivery Steps

### ✓ Step 1: Stabilize the local roadmap scaffold and register the new milestone
`docs/roadmap/` has a consistent top-level index and a reserved home for the first real milestone.

- Update `docs/roadmap/README.md` so its milestone table matches files that will actually exist.
- Add a minimal `docs/roadmap/roadmap.md` overview or equivalent supporting context to remove the current broken self-reference.
- Reserve milestone `0001-version-parsing-hardening` and describe why it targets the core gaps in `src/extract_version/version_info.py` and `src/extract_version/cli.py`.

### ✓ Step 2: Author the milestone spec and task-level roadmap documents
The new milestone folder contains a complete milestone plan plus task specs that mirror the AegisSwr structure.

- Create `docs/roadmap/0001-version-parsing-hardening/plan.md` with rationale, task table, dependency notes, and milestone-level contracts.
- Create `docs/roadmap/0001-version-parsing-hardening/status.md` with an initial not-started status table.
- Add task folders and `README.md` files for the four planned workstreams: parser contract, library hardening, inventory/selection hardening, and CLI/public-docs alignment.
- Ensure each task README calls out the concrete target files it governs, including `version_info.py`, `cli.py`, `README.md`, and the `test/` modules.

### ✓ Step 3: Fill in subtask specs and verify roadmap integrity
Each task is decomposed into actionable subtask documents, and the roadmap corpus is internally valid.

- Create the per-subtask Markdown files under each task folder with objective, affected files, behavior, tests, and success criteria.
- Cross-link milestone, task, and subtask documents using repo-root-relative links as required by `docs/roadmap/README.md`.
- Check that the subtask split stays implementation-sized rather than milestone-sized, especially for the shared parsing work in `src/extract_version/version_info.py`.
- Run the repository’s documentation link validation so the new roadmap docs do not leave broken references behind.
# Extract Version Product Roadmap

This page tracks the product-level direction for Extract Version across roadmap
milestones. The milestone/task/subtask document structure lives in
[`docs/roadmap/README.md`](/docs/roadmap/README.md); this page is the higher-level
index it references when distinguishing long-running product phases from
implementation-sized work items.

## Current focus

### Phase 1 - Harden core version parsing and selection

The first delivery phase is milestone
[`0001-version-parsing-hardening`](/docs/roadmap/0001-version-parsing-hardening/plan.md).
It is intentionally centered on the package's current value core:

- exact and well-defined version validation in
  [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- predictable extraction and sorting rules for versions embedded in names
- cleaner inventory and last-version selection behavior for mixed inputs
- CLI contract alignment in [`src/extract_version/cli.py`](/src/extract_version/cli.py)

Additional phases can be added here as more real milestones are created under
`docs/roadmap/`.
# Subtask 02 - Normalized Sort Key

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)
**Parent task:** [`01.0-version-contract-and-parser-model/README.md`](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/README.md)

## Objective

Define how parsed versions are normalized for comparison so sorting and “latest
version” selection behave deterministically across all supported version shapes.

## Affected files

- [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- [`test/test_extract_version.py`](/test/test_extract_version.py)

## Required behavior

- Specify the canonical comparison key used by `sort_versions()` and indirectly
  by `get_last_version()`.
- Define how missing components are treated when comparing different version
  shapes, for example whether `1`, `1.0`, and `1.0.0` normalize to the same
  numeric tuple.
- Keep comparison numeric by segment rather than lexicographic so `10` sorts
  after `2` and not before it.
- Decide what happens when two input strings normalize to the same comparison
  key; the roadmap should require deterministic tie handling instead of relying
  on incidental input order or filesystem order.
- Clarify that normalization is for comparison only unless another task
  explicitly chooses to rewrite returned strings.

## Tests to add or update later

- Add sort cases that mix one-, two-, and three-segment versions if the grammar
  allows them.
- Add equality/tie cases such as `1`, `1.0`, and `1.0.0` to prove the chosen
  duplicate-resolution rule.

## Success criteria

- Sorting behavior is defined once and reused by both library and CLI specs.
- Every later task can refer to one normalized comparison model instead of
  inventing its own version ordering rule.
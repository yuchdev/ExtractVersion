# Subtask 01 - Invalid-Entry Filtering

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)
**Parent task:** [`03.0-inventory-and-selection-hardening/README.md`](/docs/roadmap/0001-version-parsing-hardening/03.0-inventory-and-selection-hardening/README.md)

## Objective

Define how `available_versions()` handles names that do not contain a valid
version so the result map never exposes ambiguous empty keys by accident.

## Affected files

- [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- [`test/test_extract_version.py`](/test/test_extract_version.py)

## Required behavior

- Replace the current “empty string as a dict key” behavior with an explicit rule
  for invalid names.
- The preferred direction for this milestone is to filter invalid or versionless
  entries out of the returned mapping entirely rather than preserving them under
  `""`.
- Apply the same filtering rule regardless of whether inputs come from
  `versions_list` or `versions_path`.
- Document whether an all-invalid input source returns an empty dict or raises an
  error; later CLI subtasks should map that rule consistently for users.

## Tests to add or update later

- Add mixed valid/invalid list inputs to
  [`test/test_extract_version.py`](/test/test_extract_version.py).
- Add at least one filesystem-backed case where a directory contains both valid
  and invalid names and only the valid ones survive.

## Success criteria

- `available_versions()` no longer leaks `""` keys into its public output.
- Invalid-entry handling is documented once and reused by selection and CLI work.
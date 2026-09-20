# Subtask 03 - Pattern Capture Rules

**Parent milestone:** [`0001-version-parsing-hardening/plan.md`](/docs/roadmap/0001-version-parsing-hardening/plan.md)
**Parent task:** [`02.0-library-validation-and-extraction/README.md`](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/README.md)

## Objective

Define how `pattern`-based extraction behaves so ambiguous strings and invalid
regular-expression captures do not rely on undocumented assumptions.

## Affected files

- [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- [`test/test_extract_version.py`](/test/test_extract_version.py)

## Required behavior

- Require `pattern` to identify exactly one candidate version capture, matching
  the CLI help text that already says “regex with one capture group”.
- Document how the library should behave when the regex does not match, has no
  capture group, or captures a string that fails exact version validation.
- Route any captured value through the same exact parser used for non-pattern
  extraction so pattern-based paths cannot bypass validation.
- Specify at least one disambiguation case like
  `PyCharm-2018.1.2-windows-10.0` where the pattern is required because default
  extraction alone is ambiguous.
- Decide whether malformed regex patterns should raise `re.error` as normal or be
  converted into an empty result; whichever rule is chosen must be tested and
  documented.

## Tests to add or update later

- Add cases for no-match, wrong-capture, multi-number, and invalid-capture
  scenarios in [`test/test_extract_version.py`](/test/test_extract_version.py).
- Add CLI coverage for `extract --pattern` around the same edge cases if the user
  experience changes.

## Success criteria

- Pattern-based extraction is precise, documented, and consistent with the
  non-pattern parser.
- Ambiguous multi-number strings no longer depend on whatever regex happens to
  match first.
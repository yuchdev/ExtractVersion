# 01 - Supported Version Shapes

**Parent task:** [`01.0-version-contract-and-parser-model/README.md`](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/README.md)
**State:** ⬜ Not started
**Depends on:** -
**Blocks:** 02, 03

## Objective

Define the supported version grammar for Extract Version so the public docs,
library functions, and CLI commands stop relying on implicit regex behavior.

## Files

- **Modify** [`src/extract_version/version_info.py`](/src/extract_version/version_info.py)
- **Modify** [`README.md`](/README.md)
- **Modify** [`test/test_extract_version.py`](/test/test_extract_version.py)

## Required behavior

- Decide whether the public contract supports `X`, `X.Y`, and `X.Y.Z`, or only a
  subset of those forms; the decision must reconcile the current docstring for
  `extract_version()` with the actual regex behavior in `version_info.py`.
- Treat each segment as a base-10 integer token separated by literal dots, with
  no embedded spaces, signs, or alphabetic suffixes.
- Document whether leading zeroes are accepted as input and whether they are
  preserved in returned strings while still comparing numerically.
- Specify match precedence when more than one candidate could be found in the
  same string; prefer the most specific valid version shape rather than the
  shortest numeric fragment.
- State clearly whether extraction may match versions embedded inside larger
  strings like `PyCharm-2020.1.0` and when a pattern is required to disambiguate.

## Tests to add or update later

- Extend [`test/test_extract_version.py`](/test/test_extract_version.py) with
  examples for each supported shape and for rejected near-misses such as
  `1.0beta`, `v1.0`, or malformed dotted tokens.
- Add README examples that mirror the accepted shapes exactly.

## Success criteria

- [ ] There is one written grammar that every later roadmap subtask can reference.
- [ ] The supported shapes in docs and tests match the eventual parser contract
      with no contradiction between code comments and public examples.
</content>

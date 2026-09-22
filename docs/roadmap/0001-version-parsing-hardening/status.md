# Milestone 0001 - Version Parsing and Selection Hardening - Status

Tracks progress against [plan.md](/docs/roadmap/0001-version-parsing-hardening/plan.md).
Updated as each task lands.

**Milestone status: ✅ All 4 tasks / 14 subtasks complete.** A milestone-wide
pre-PR review (feature-reviewer + security-auditor over the full accumulated
diff, not just the final task) ran after Task 04.0 landed - see
[Milestone-wide pre-PR review](#milestone-wide-pre-pr-review) below.

## Current status

| Task | Name                               | Status         | Notes |
|------|-------------------------------------|----------------|-------|
| 01.0 | Version Contract and Parser Model  | ✅ Complete | Grammar, sort-key, and compatibility-policy contract landed; see summary below. |
| 02.0 | Library Validation and Extraction  | ✅ Complete | Shared parse helper, exact validation, pattern-capture contract, and test suite reorg landed; see summary below. |
| 03.0 | Inventory and Selection Hardening  | ✅ Complete | Invalid-entry filtering confirmed/hardened, source-precedence and no-source-provided rules added, fixtures mirrored into CLI tests; see summary below. |
| 04.0 | CLI Contract and Public Docs        | ✅ Complete | Exit-code contract documented, numeric output ordering fixed, README/examples audited, CLI test suite extended; see summary below. |

**Legend:** ✅ Complete · 🔶 In progress / partial · ⬜ Not started

**Current gate status:** All four tasks are complete and have shipped product
code (`src/extract_version/version_info.py`, `cli.py`, `README.md`, and both
test files). Tasks were implemented strictly sequentially
(`01.0 → 02.0 → 03.0 → 04.0`); see
[plan.md § Dependency notes](/docs/roadmap/0001-version-parsing-hardening/plan.md#dependency-notes).
Test suite: `test/test_extract_version.py` grew from 9 to 45 tests;
`test/test_cli.py` grew from 17 to 60 tests.

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

### Task 01.0 - Version Contract and Parser Model (✅ Complete)

All three subtasks landed. See [`01.0-version-contract-and-parser-model/README.md`](/docs/roadmap/0001-version-parsing-hardening/01.0-version-contract-and-parser-model/README.md)
for scope.

**Delivered:**
- **Subtask 01 (supported version shapes):** grammar contract fixed to exactly
  `X.Y` and `X.Y.Z` (no bare single-integer version), reconciling
  `extract_version()`'s docstring with the actual regex behavior.
  `validate_version()` fixed from a prefix match (`re.match`) to an exact
  match (`re.fullmatch`), rejecting trailing/leading garbage
  (`"1.0.0abc"`, `"1.0beta"`). Leading zeros documented as accepted/preserved
  and compared numerically. Match precedence (`X.Y.Z` over `X.Y`) and
  embedded/pattern-disambiguation behavior documented explicitly.
- **Subtask 02 (normalized sort key):** new `_comparison_key()` helper
  zero-pads every version to a fixed width of 3 segments so differing-length
  shapes that share a prefix tie (`"1.0"` == `"1.0.0"`), with a deterministic
  secondary tie-break by the original version string (not input/filesystem
  order). `sort_versions()` remains comparison-only - returned strings are
  unchanged.
- **Subtask 03 (compatibility policy):** `available_versions()` now filters
  out unparseable entries instead of collapsing them onto a shared `""` key
  (which used to crash the sort with `ValueError`); `get_last_version()` now
  raises a descriptive `ValueError` on an empty/all-unparseable inventory
  instead of a bare `IndexError`. Both `version_info.py`'s module docstring
  and `README.md` now carry a full "Compatibility Policy" section stating
  what's preserved (happy paths, permissive embedded extraction, duplicate-
  resolution determinism) vs. intentionally tightened (exact validation,
  empty-key removal, explicit error), with a migration note for the
  `validate_version` change.

**Key implementation decisions** (resolved via user confirmation mid-implementation,
since they shape every later task's parser/sort behavior): no bare-integer
version support; zero-pad missing segments to tie rather than always ranking
shorter-shape strictly lower; tie-break by original string rather than input
order; filter (don't collapse) unparseable inventory entries; raise a clear
error rather than a bare `IndexError` on no-version-found.

**Tests:** `test/test_extract_version.py` grew from 9 to 25 tests;
`test/test_cli.py` grew from 17 to 21 tests. Both suites green
(`python test/test_extract_version.py`, `python test/test_cli.py`).
`flake8 --select=E9,F63,F7,F82` clean. `/pr-review` verdict: **APPROVE**
(feature-reviewer LGTM, security-auditor PASS, no blocking findings).

**Deferred / handed off (not blocking, out of this task's scope):**
- `available_versions()` still last-write-wins on an exact same-string key
  collision (two distinct names extracting to the identical version string);
  order-dependent when sourced via `versions_path`/`os.listdir()`. Documented
  as an explicit boundary of the new determinism guarantee rather than fixed
  here - it's Task 03.0's territory (see handoff note below).
- `versions_path` vs `versions_list` priority in `available_versions()`/
  `get_last_version()` is documented but was never asserted by a test -
  handed to Task 03.0.
- `get_last_version()`'s return-value shape (original name vs. normalized key)
  is covered by fixture-dir tests but not by a plain `versions_list` case -
  handed to Task 03.0.
- A pre-existing `IndexError` when a caller-supplied `--pattern`/`pattern=`
  matches but has no capture group (`match.group(1)` on a group-less pattern)
  is unchanged by this task; flagged by both feature-reviewer and
  security-auditor as a LOW-severity, non-blocking robustness gap for a
  future CLI/library task to address.

### Task 02.0 - Library Validation and Extraction (✅ Complete)

All four subtasks landed. See [`02.0-library-validation-and-extraction/README.md`](/docs/roadmap/0001-version-parsing-hardening/02.0-library-validation-and-extraction/README.md)
for scope.

**Delivered:**
- **Subtask 01 (exact `validate_version()`):** confirmed the exact-match
  behavior was already correct from Task 01.0; closed the two test-coverage
  gaps the spec named (a `"1.0.0-linux"` near-miss case, and CLI-level
  regression coverage for `validate` rejecting valid-prefix-plus-junk
  strings). No production code change needed.
- **Subtask 02 (shared parse helper):** consolidated parsing into two private
  helpers - `_normalize_key()` (permissive int-cast + zero-pad, no grammar
  gate) and `_parse_version()` (grammar-gated via `re.fullmatch`, returns a
  `_ParsedVersion` NamedTuple or `None`) - deliberately split so
  `sort_versions()` keeps accepting out-of-grammar bare integers (e.g.
  `"20"`, matching the pre-existing `test_sort_versions`) while
  `validate_version()` stays strictly grammar-gated. Pure refactor: all
  pre-existing tests passed unchanged.
- **Subtask 03 (pattern capture rules):** `extract_version(pattern=...)` now
  has a documented four-case contract - no match -> `""`; wrong capture-group
  count (0 or 2+) -> raises `PatternArityError` (a `ValueError` subclass,
  message "pattern must contain exactly one capture group"); invalid regex
  syntax -> `re.error` propagates naturally; captured-but-invalid -> `""`.
  This directly resolved the LOW-severity finding from Task 01.0's
  `/pr-review` (a bare, uncaught `IndexError` on a capture-group-less
  pattern). All three CLI subcommands accepting `--pattern`
  (`extract`/`available`/`last-version`) now catch both exception types and
  print a friendly stderr message instead of a raw traceback.
- **Subtask 04 (library tests):** reorganized the suite per this task's
  explicit "test public functions, not private internals" convention -
  removed 4 tests asserting directly on `_normalize_key`/`_parse_version`/
  `_ParsedVersion` and replaced them with public-function equivalents that
  preserve the same invariants; closed six specific coverage gaps (CLI
  `validate` no-input/mixed-input cases, `sort_versions()`'s 4+-segment and
  non-numeric-segment edge behavior, plain-text `available` output,
  `extract`'s multi-name pattern-error short-circuit).

**Key implementation decisions** (resolved via user confirmation
mid-implementation): drop the "gate everything through one strict-grammar
helper" approach in favor of splitting permissive normalization from
grammar-gated validation, to avoid breaking `sort_versions()`'s existing
bare-integer support; convert subtask 02's private-helper tests to
public-function equivalents per subtask 04's stated convention; pattern-arity
errors (0 or 2+ capture groups) raise a clear, documented exception rather
than being converted to an empty `""` result, and invalid regex syntax is
allowed to propagate as Python's own `re.error` rather than being swallowed.

**Tests:** `test/test_extract_version.py` grew from 25 to 37 tests;
`test/test_cli.py` grew from 21 to 34 tests. Both suites green. `flake8
--select=E9,F63,F7,F82` clean. `/pr-review` verdict: **APPROVE**
(feature-reviewer LGTM, security-auditor PASS). Two non-blocking review
findings - both about code this task introduced - were fixed before closing:
a fragile `"capture group" in str(error)` string-routing heuristic in the CLI
(replaced with a dedicated `PatternArityError` exception type) and missing
type annotations on the three new private helpers.

**Deferred / handed off (not blocking, out of this task's scope):**
- `_print()`'s plain-text (non-`--json`) formatting of `available`'s dict
  output sorts lexicographically (`sorted(..., key=lambda item: item[0])`),
  not numerically - `"1.10"` would sort before `"1.9"`. Pre-existing, not
  introduced by this task; flagged by feature-reviewer as a separate,
  non-blocking issue. Handed to Task 04.0 (CLI Contract and Public Docs,
  specifically its `02-output-format-rules.md` subtask).
- Public function signatures (`validate_version`, `sort_versions`,
  `extract_version`, `available_versions`, `get_last_version`) still lack
  type annotations - pre-existing across the whole module, not introduced by
  this task. A follow-up annotation pass would need its own task/subtask.
- The same-string key-collision finding from Task 01.0's handoff (below)
  remains open and unaffected by this task's work - still Task 03.0's
  territory.

### Task 03.0 - Inventory and Selection Hardening (✅ Complete)

All three subtasks landed. See [`03.0-inventory-and-selection-hardening/README.md`](/docs/roadmap/0001-version-parsing-hardening/03.0-inventory-and-selection-hardening/README.md)
for scope.

**Delivered:**
- **Subtask 01 (invalid-entry filtering):** confirmed `available_versions()`'s
  filtering (already landed in Task 01.0) applies identically to
  `versions_list` and `versions_path` - same shared loop, no source-specific
  case. Closed the filesystem-backed coverage gap Task 01.0's handoff called
  out: new fixtures `mixed/` (valid+invalid mix), `all-invalid/` (all-invalid
  boundary via path), and `filtered/` (dir-name-vs-version-key distinction
  via path) prove the `versions_path` code path filters and resolves
  identically to `versions_list`.
- **Subtask 02 (last-version selection rules):** closed the
  `versions_path`-wins-over-`versions_list` precedence gap Task 01.0's
  handoff called out - new tests cover both a populated `versions_path`
  winning over a populated `versions_list`, and (the sharper case) an EMPTY
  `versions_path` still winning over a populated `versions_list` (using
  `tempfile.TemporaryDirectory()`). Also closed an undocumented failure mode
  found along the way: `available_versions()`/`get_last_version()` with
  NEITHER `versions_list` nor `versions_path` provided used to raise a raw
  `TypeError` from iterating `None`; now raises a clear
  `ValueError("either versions_list or versions_path must be provided")`,
  consistent with this module's established "documented errors, not
  incidental built-in exceptions" precedent (`PatternArityError`, the
  empty-inventory `ValueError`). Also proved the duplicate-tie-break winner
  is independent of plain-list input order, not just filesystem order.
- **Subtask 03 (fixtures and tests):** mirrored all four fixture-backed cases
  (`mixed/`, `all-invalid/`, `filtered/`, `duplicates/`) into
  `test/test_cli.py`'s `available --path`/`last-version --path` tests (8 new
  CLI tests), closing Task 01.0's handoff note about
  `get_last_version()`'s return-value shape only being exercised via fixture
  directories, not via CLI.

**Key implementation decisions** (resolved via user confirmation for the one
genuinely open design question; the "raise a clear ValueError" fix followed
this module's already-established precedent directly, so it didn't need a
fresh decision): none required a fresh fork this task - subtask 01's
behavior was already fully correct from Task 01.0, and subtask 02's new
guard applied an existing pattern rather than inventing a new one.

**Tests:** `test/test_extract_version.py` grew from 37 to 45 tests;
`test/test_cli.py` grew from 34 to 42 tests. Both suites green. `flake8
--select=E9,F63,F7,F82` clean. `/pr-review` verdict: **APPROVE**
(feature-reviewer LGTM, security-auditor PASS). Two non-blocking cosmetic
findings (duplicate `except` clauses in `_cmd_last_version`; an
undocumented invariant protecting the new `ValueError` message from being
silently swallowed) were fixed before closing.

**Note on the same-string key-collision finding** (from Task 01.0's
handoff): `available_versions()` still last-write-wins when two DISTINCT
names extract to the IDENTICAL version string (e.g. `"1.0"` and `"app-1.0"`
both extracting to `"1.0"`) - order-dependent, not deterministic. This is
distinct from the "two names normalize to the same padded key" case (e.g.
`"1.0"`/`"1.0.0"`), which this task's subtask 02 makes fully deterministic.
The same-string case was deliberately NOT changed: it is explicitly
documented (module docstring, since Task 01.0) as outside the determinism
guarantee, and fixing it would require a new tie-break rule this milestone's
subtask specs never specify (e.g. "reject on collision" vs. "pick
alphabetically first" vs. "keep last-write-wins as documented"). Flagged
again by this task's own test-gap review as P2/low-priority precisely
because it's already a documented non-guarantee, not an oversight. If this
should become a hard requirement, it needs a follow-up subtask with an
explicit tie-break decision, not a silent fix.

### Task 04.0 - CLI Contract and Public Docs (✅ Complete)

All four subtasks landed - the final task of this milestone. See
[`04.0-cli-contract-and-public-docs/README.md`](/docs/roadmap/0001-version-parsing-hardening/04.0-cli-contract-and-public-docs/README.md)
for scope.

**Delivered:**
- **Subtask 01 (CLI error contract):** documented the exit-code contract
  explicitly in `cli.py`'s module docstring (also feeds `--help` via
  `description=__doc__`): `0` full success, `1` semantic/partial failure,
  `2` missing/invalid input. Confirmed and formally documented the existing
  partial-success policy (`extract`/`validate` emit successes to stdout
  alongside per-name stderr failures) as the deliberate contract, not an
  accident. Closed two test gaps (`extract`'s own partial-success case,
  `sort`'s exit-1 path had no test at all), plus two more from its own
  test-gap review (exact per-name stderr-line-count assertion; argparse's
  own exit-2 behavior for unknown/missing subcommands).
- **Subtask 02 (output format rules):** fixed the lexicographic-vs-numeric
  bug handed off from Task 02.0 - `available`'s mapping output (plain-text
  AND `--json`) now orders keys via the public `sort_versions()` rather than
  raw string comparison, so `"1.9"` now correctly precedes `"1.10"`. Routed
  through the public API rather than reaching into `version_info.py`'s
  private helpers (a layering-boundary concern). Documented the full
  plain-text/JSON output-shape contract in both `cli.py` and `README.md`.
- **Subtask 03 (README and examples):** audited `README.md` and all three
  `src/examples/*.py` scripts against the fully-hardened contract by
  actually running them; found everything already accurate from subtasks
  01/02's work except one real gap - the pattern-capture error contract
  (`PatternArityError`/`re.error`/the two `""` cases) was implemented and
  tested but never surfaced to README readers. Added a "Pattern error
  contract" subsection.
- **Subtask 04 (CLI tests):** closed the three remaining named gaps -
  `validate --json` and `last-version --json` had zero test coverage; no
  CLI-level test proved `--path` wins over positional names when both are
  given to `available`/`last-version`. No production-code bug found behind
  any of these coverage gaps.

**Key implementation decisions** (resolved via user confirmation
mid-implementation): keep partial-success semantics for multi-name commands
rather than switching to all-or-nothing (a real, deliberate fork the spec
called out); order `available`'s mapping output by the numeric version-sort
contract rather than lexicographically (fixes the Task 02.0 handoff item).

**Tests:** `test/test_extract_version.py` stayed at 45 tests (this task
didn't touch library-level logic); `test/test_cli.py` grew from 42 to 60
tests. Both suites green. `flake8 --select=E9,F63,F7,F82` clean.

**Deferred / handed off (not blocking, out of this task's scope):** a
handful of low-priority test-gap P2 items (exit-2 stdout-empty assertions,
`extract --json` partial-failure test, `_read_names` TTY-branch, a
three-segment mapping-ordering test, duplicates-fixture tie-break order via
`_print`) were not closed - all cosmetic/low-risk per their respective
test-gap reviews.

## Milestone-wide pre-PR review

With Task 04.0 landed, this is the last task of the milestone - since nothing
was committed mid-stream this session, the working tree at this point holds
all four tasks' combined changes as one diff. A dedicated, holistic
pre-PR review ran over that full diff (not a re-run of each task's own
already-approved review), specifically checking for whole-milestone
coherence, redundancy between incremental patches, and any interaction
effect between tasks that a per-task review couldn't see.

**Verdict:** feature-reviewer **LGTM**, security-auditor **PASS_WITH_FOLLOWUP**.

**One genuine cross-cutting finding, independently caught by both reviewers**
(the kind of gap a whole-diff pass is for): `available --path`/
`last-version --path` never caught `OSError` from `os.listdir()` - a
nonexistent path, a path pointing at a file instead of a directory, or a
permission-denied directory all raised a raw Python traceback (with absolute
internal source paths) instead of the friendly stderr message + exit code 1
every other error path in this CLI now produces. This directly contradicted
the exit-code/stderr contract Task 04.0 had just finished documenting.
**Fixed:** both CLI functions now catch `OSError` alongside `ValueError`/
`re.error`/`PatternArityError`, with regression tests for a nonexistent path
and a not-a-directory path on both commands.

**Also fixed** (small doc-wording nits from the same review): a slightly
overspecified claim in `cli.py`'s docstring about pattern errors always
producing exactly one stderr line; a missing `:raises ValueError:` note on
`sort_versions()`'s docstring; a slightly misleading "compare as `1.0.0`"
phrasing in README's Compatibility Policy section (duplicate-normalized
versions tie/normalize to the same numeric key, they don't have one
canonical string form). Plus one minor test gap (plain-text `available`
output on an all-invalid directory had no test - only the `--json` case did).

**Confirmed still accurately deferred** (not silently fixed or silently
left broken): the same-string key-collision non-guarantee in
`available_versions()`, and the still-missing type annotations on all five
public functions - both reviewed once more at the whole-milestone level and
found unchanged and accurately documented as intentionally out of scope.

**Final state:** `test/test_extract_version.py` at 45 tests,
`test/test_cli.py` at 60 tests, both green; `flake8 --select=E9,F63,F7,F82`
clean across the whole tree.
</content>

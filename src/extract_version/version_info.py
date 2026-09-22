import os
import re
from typing import NamedTuple, Optional

__doc__ = """The module offers following functionality:
* Fetching version string from the string or name of the directory
* Validating version string
* Sorting config and application directories that contain versions in its name

Version grammar contract
-------------------------
This module is the canonical reference for the version grammar every other part
of the package (CLI, sorting, inventory helpers) relies on. The contract is:

* Supported shapes: exactly two forms are recognized as versions,
  "X.Y" (two segments, e.g. "1.0") and "X.Y.Z" (three segments, e.g. "2020.1.0").
  A bare single integer such as "1" or "2020" is NOT a version and is never
  matched or accepted.
* Segment tokens: each segment is a base-10 integer made of ASCII digits only,
  separated by literal dots. No spaces, signs (+/-), or alphabetic suffixes are
  permitted inside or around a version token; strings like "v1.0", "1.0beta",
  or "1.0.0abc" are not valid versions.
* Leading zeros: accepted as input and preserved verbatim in the extracted or
  returned string (e.g. "1.00" stays "1.00", "0.01" stays "0.01"). They are
  significant only as text; sorting compares each dot-segment numerically
  (cast to int), so "1.00" and "1.0" compare equal segment-for-segment.
* Match precedence: when a string could satisfy more than one shape, the most
  specific valid shape wins. The three-segment "X.Y.Z" form is tried before the
  two-segment "X.Y" form, so "2020.1.0" is read as one three-segment version
  rather than the shorter "2020.1" fragment.
* Embedded matching: extract_version() may match a version embedded inside a
  larger string (e.g. "PyCharm-2020.1.0" -> "2020.1.0") without an explicit
  pattern. An explicit regex pattern (with one capture group) is required only
  to disambiguate when the string contains more than one numeric-group
  candidate, e.g. a version plus an OS build number
  ("PyCharm-2018.1.2-windows-10.0").

Examples:
1. We fetch version "2020.1.0" from string "PyCharm-2020.1.0", or version "1.0" from "my_program_v1.0".
extract_version(version_string="PyCharm-2020.1.0")
> "2020.1.0"
extract_version(version_string="my_program_v1.0")
> "1.0"

2. Versions of PyCharm are named like ["PyCharm-2020.1.0", "PyCharm-2018.2.0", "PyCharm-2018.1.2"]
should be sorted like ["PyCharm-2018.1.2", "PyCharm-2018.2.0", "PyCharm-2020.1.0"]
sort_versions(["PyCharm-2018.1.2", "PyCharm-2018.2.0", "PyCharm-2020.1.0"])
> ["PyCharm-2018.1.2", "PyCharm-2018.2.0", "PyCharm-2020.1.0"]

3. In edge cases with more than one pattern, e.g. "PyCharm-2018.1.2-windows-10.0",
we should provide a clue where the version should be extracted from,
in a form of a regex-pattern, like "PyCharm-(.*)-windows-10.0".
Call of such function should look like:
extract_version(version_string='PyCharm-2018.1.2-windows-10.0', pattern='PyCharm-(.*)-windows-10.0')
> "2018.1.2"

Compatibility Policy
--------------------
Parser hardening preserves the documented happy paths while tightening a few
behaviors that used to be silently permissive. This section records which is
which so the shifts are deliberate and user-visible rather than surprising.

Preserved for compatibility:

* Supported happy paths are unchanged. Every "X.Y" and "X.Y.Z" case that was
  valid before is still valid and returns the same result (leading zeros are
  still accepted and preserved verbatim).
* Permissive embedded extraction remains the default. extract_version() with
  no pattern may still match a version embedded anywhere inside a larger string
  (e.g. "PyCharm-2020.1.0" -> "2020.1.0"). An explicit regex pattern (with one
  capture group) is required only to disambiguate when the string holds more
  than one numeric-group candidate (e.g. a version plus an OS build number,
  "PyCharm-2018.1.2-windows-10.0"); it is never required for the single-version
  case.
* Duplicate normalized versions resolve deterministically and identically
  regardless of input source. When two distinct inventory entries extract to
  different but normalization-equal version strings (e.g. "1.0" and "1.0.0",
  which both pad to (1, 0, 0)), the winner is decided by sort_versions()'s
  string tie-break, a pure function of the version strings themselves. The
  same set of names therefore produces the same winner whether it arrives via
  versions_list or via versions_path (os.listdir()), because available_versions()
  builds the same dict either way before sorting ever runs. This guarantee
  covers only entries with different extracted strings: if two distinct names
  extract to the exact same version string (e.g. "1.0" and "app-1.0" both
  extracting to "1.0"), available_versions()'s dict construction still keeps
  only one of them, and which one is order-dependent (last-write-wins) rather
  than covered by this determinism guarantee.

Intentionally tightened (stricter than before):

* Exact validation. validate_version() now requires a full-string match
  (re.fullmatch) instead of a prefix match (re.match). Trailing or leading
  non-version characters are rejected. Migration note: code that relied on
  validate_version("1.0.0abc") returning a truthy value will now get "".
* Empty-string inventory keys removed. available_versions() no longer maps
  every unparseable name onto a single bogus "" key. Names whose version cannot
  be extracted are filtered out of the returned mapping, so downstream sorting
  and get_last_version() only ever see valid versions (previously a single
  unparseable entry could crash sort_versions() with ValueError from int("")).
* Explicit error when no valid version is found. get_last_version() raises a
  descriptive ValueError when the inventory is empty or every entry is
  unparseable, instead of the previous bare IndexError from indexing an empty
  sorted list.
* Explicit error unless a pattern declares exactly one capture group.
  extract_version(pattern=...) raises a descriptive ValueError when the pattern
  matches but does not declare exactly one capture group -- both zero groups
  (e.g. a plain or non-capturing "(?:...)" pattern, previously a bare IndexError
  from match.group(1)) and two or more groups (previously silently returning
  match.group(1) and ignoring the rest). A pattern that simply does not match
  still returns "" (no version found), and an invalid regex still raises re.error
  unchanged.
"""

REG_V1 = re.compile(r"\d+\.\d+\.\d+")
REG_V2 = re.compile(r"\d+\.\d+")

# The grammar contract (see module docstring) caps a version at three segments
# ("X.Y.Z"), so every comparison key is padded out to this fixed width.
_SEGMENT_COUNT = 3


class PatternArityError(ValueError):
    """
    Raised when an ``extract_version`` pattern matches but does not declare
    exactly one capture group.

    Subclasses :class:`ValueError` so existing ``except ValueError`` handlers
    keep catching it unchanged, while callers that need to distinguish this
    specific pattern-arity failure from other value errors can catch it
    directly instead of sniffing the exception message text.
    """


class _ParsedVersion(NamedTuple):
    """
    A validated, normalized version, produced by :func:`_parse_version`.

    Carries both representations so consumers never have to reparse the same
    candidate: the untouched matched text and the numeric comparison key.

    :ivar original: the original matched version string, unchanged (leading
        zeros preserved verbatim)
    :ivar key: the normalized fixed-width numeric tuple from
        :func:`_normalize_key`, suitable for numeric comparison
    """

    original: str
    key: tuple[int, ...]


def _normalize_key(candidate: str) -> tuple[int, ...]:
    """
    Normalize a dot-separated integer string into a fixed-width numeric tuple.

    This is the low-level normalization primitive: it applies no grammar or
    shape gate, so it accepts any dot-separated run of base-10 integers,
    including single-segment values such as "20". Each segment is cast to
    ``int`` (so comparison is numeric per segment and leading zeros compare
    equal, e.g. "1.00" and "1.0" both yield ``(1, 0, 0)``), then the tuple is
    padded with trailing zeros to a fixed width of three so differing-length
    shapes tie when their shared prefix matches.

    Because it applies no grammar gate, this primitive neither truncates nor
    rejects out-of-contract input: a 4+ segment string keeps all its segments
    (e.g. "1.2.3.4" yields the un-truncated ``(1, 2, 3, 4)``), and a non-numeric
    or empty segment (e.g. "1.x" or "") propagates the ``ValueError`` from
    ``int()``. Callers such as :func:`sort_versions` are therefore expected to
    feed already-valid versions; grammar enforcement lives in
    :func:`_parse_version`.

    Normalization is for comparison only; the input string is never rewritten.
    :param candidate: a dot-separated integer string such as "1.0", "2020.1.0"
        or a bare "20"
    :return: the padded numeric tuple, e.g. "1.0" -> ``(1, 0, 0)``
    """
    segments = [int(segment) for segment in candidate.split(".")]
    padding = [0] * (_SEGMENT_COUNT - len(segments))
    return tuple(segments + padding)


def _parse_version(candidate: str) -> Optional[_ParsedVersion]:
    """
    Validate a standalone candidate against the grammar and normalize it.

    This is the single internal parsing entry point for standalone version
    strings: it applies the grammar gate (the two supported shapes "X.Y.Z" or
    "X.Y", via ``re.fullmatch``) that :func:`validate_version` and the
    pattern-capture path of :func:`extract_version` rely on, and pairs the
    validated string with its normalized comparison key so callers never
    reparse it. It is deliberately distinct from the low-level
    :func:`_normalize_key`, which applies no grammar gate and stays permissive
    for :func:`sort_versions`.
    :param candidate: a standalone string to validate as a whole version
    :return: a :class:`_ParsedVersion` carrying the original matched string and
        its normalized key when the candidate is a valid version, or ``None``
        when it is not
    """
    if REG_V1.fullmatch(candidate) or REG_V2.fullmatch(candidate):
        return _ParsedVersion(original=candidate, key=_normalize_key(candidate))
    return None


def _comparison_key(version_string: str) -> tuple[tuple[int, ...], str]:
    """
    Build the canonical comparison key for a single version string.

    The key is a ``(numeric_tuple, original_string)`` pair:

    * ``numeric_tuple`` casts each dot-separated segment to ``int`` (so
      comparison is numeric per segment, e.g. "10" sorts after "2", and
      leading zeros are numerically equal, e.g. "1.00" == "1.0"), then pads
      the tuple with trailing zeros to a fixed width of three. Padding makes
      differing-length shapes tie when their shared prefix matches, so "1.0"
      and "1.0.0" both normalize to ``(1, 0, 0)``.
    * ``original_string`` is the un-normalized input, used only as a
      deterministic secondary sort key so entries whose numeric tuples are
      equal break ties by their original text (lexicographically) rather than
      by incidental input order or filesystem ordering.

    Normalization is for comparison only; the string itself is never rewritten.
    The numeric-tuple math is delegated to :func:`_normalize_key`, which stays
    permissive (no grammar gate) so single-segment inputs such as "20" still
    sort, unlike the stricter :func:`_parse_version` used for validation.
    :param version_string: a version string such as "1.0" or "2020.1.0"
    :return: a ``(padded_numeric_tuple, original_string)`` comparison key
    """
    return _normalize_key(version_string), version_string


def validate_version(version_string):
    """
    Validate that a string is *exactly* a version.

    Accepts only the two supported shapes, "X.Y.Z" or "X.Y" (base-10 integer
    segments separated by literal dots). The whole string must be a version:
    trailing or leading non-version characters (e.g. "1.0beta", "v1.0",
    "1.0.0abc") are rejected. Leading zeros are accepted and preserved. See the
    module docstring for the full grammar contract.
    :param version_string: exact version string, e.g. "1.0.0", "1.0"
    :return: version string if valid, "" otherwise
    """
    parsed = _parse_version(version_string)
    return parsed.original if parsed is not None else ""


def sort_versions(versions_list, descending=False):
    """
    Sort a list of version strings by their canonical comparison key.

    Accepts a list of versions such as ['1.0.0', '1.0']. Sorting uses the
    normalized comparison key from ``_comparison_key``:

    * Each version's dot-separated segments are cast to ``int`` and the segment
      tuple is padded with trailing zeros to a fixed width of three, so missing
      trailing segments are treated as ``0`` and differing-length shapes tie
      when their shared prefix matches (e.g. "1.0" and "1.0.0" compare equal).
    * Comparison is numeric per segment, so "10" sorts after "2", and leading
      zeros are numerically equal (e.g. "1.00" and "1.0" compare equal).
    * Entries whose padded numeric tuples are equal are ordered deterministically
      by their original string (lexicographically) rather than by input order.

    Normalization is for comparison only: the returned list holds the original
    input strings unchanged (no zero-padding leaks into the result).
    :param versions_list: list of version strings, e.g. ['1.0.0', '1.0']
    :param descending: sort in descending order when True (default: ascending)
    :return: the same list sorted in place
    :raises ValueError: if any version string contains a non-integer segment
        (the ``int()`` cast in ``_normalize_key`` fails)
    """
    assert isinstance(versions_list, list)
    versions_list.sort(key=_comparison_key, reverse=descending)
    return versions_list


def extract_version(*, version_string, pattern=None):
    """
    Extract a version embedded in a string, with or without a known pattern.

    Finds a version of kind "X.Y.Z" or "X.Y" (the only supported shapes; a bare
    integer like "1" is never matched). The three-segment "X.Y.Z" form takes
    precedence over the two-segment "X.Y" form. A version may be embedded inside
    a larger string (e.g. "PyCharm-2020.1.0" -> "2020.1.0"); an explicit pattern
    is only needed to disambiguate when the string holds more than one numeric
    candidate (e.g. a version plus an OS build number). Leading zeros are
    preserved verbatim. See the module docstring for the full grammar contract.
    Pattern-capture contract (see the module docstring's grammar contract): when
    ``pattern`` is given it must contain exactly one capture group locating the
    version candidate. The behaviors are:

    * No match at all (the regex finds nothing in ``version_string``): returns ""
      -- this is "no version found", not a caller error.
    * Match without exactly one capture group (zero groups, e.g. a plain or
      non-capturing ``(?:...)`` pattern, or two or more groups): raises
      ``PatternArityError`` (a ``ValueError`` subclass) because the pattern does
      not identify exactly one candidate to validate.
    * Invalid regex syntax in ``pattern``: the ``re.error`` from ``re.search``
      propagates unchanged; it is a clear, self-documenting exception.
    * Captured text that fails exact version validation: routes through
      ``validate_version`` (the same grammar gate as non-pattern extraction) and
      returns "".
    :param version_string: string containing the version, e.g. "PyCharm-2018.1.2-linux", "my_program_v1.0"
    :param pattern: the exact regex of the name that contains version, e.g. "PyCharm-(.*)-linux"
    :raises PatternArityError: if ``pattern`` matches but does not contain
        exactly one capture group. This is a ``ValueError`` subclass, so callers
        doing ``except ValueError`` still catch it unchanged, while callers that
        need to discriminate this case can catch ``PatternArityError`` directly.
    :raises re.error: if ``pattern`` is not a valid regular expression
    """
    if pattern is not None:
        match = re.search(pattern, version_string)
        if match is None:
            return ""
        if match.re.groups != 1:
            raise PatternArityError("pattern must contain exactly one capture group")
        return validate_version(match.group(1))

    if version := REG_V1.findall(version_string):
        return version[0]
    elif version := REG_V2.findall(version_string):
        return version[0]
    else:
        return ""


def available_versions(*, versions_list=None, versions_path=None, pattern=None):
    """
    All available versions of the program.

    Names whose version cannot be extracted (``extract_version`` returns "")
    are filtered out of the mapping rather than collapsed onto a single bogus
    "" key, so downstream sorting and ``get_last_version`` only ever see valid
    versions. See the module docstring's Compatibility Policy for details.
    :param versions_list: list of application directories containing version
    :param versions_path: this directory contains all the versions of the program
    :param pattern: the pattern of the name that contains version, e.g. "my_program_v{}"
    :return: dictionary of pairs (version, path)
    :raises ValueError: if neither ``versions_list`` nor ``versions_path`` is
        provided (both left ``None``), there is no inventory to inspect. Note the
        related but distinct empty-inventory case raised by ``get_last_version``
        when an inventory is supplied but yields no valid version.
    """
    if versions_list is None and versions_path is None:
        raise ValueError("either versions_list or versions_path must be provided")
    if versions_path is not None:
        versions_list = os.listdir(versions_path)
    version_dirs = {}
    for dir_name in versions_list:
        version = extract_version(version_string=dir_name, pattern=pattern)
        if version:
            version_dirs[version] = dir_name
    return version_dirs


def get_last_version(*, versions_list=None, versions_path=None, pattern=None):
    """
    Get the last version of the program.
    Able to accept list of versions or path to the directory with versions,
    in the latter case the path has priority over list.

    Raises ``ValueError`` when the inventory is empty or every entry is
    unparseable (no valid version to return). See the module docstring's
    Compatibility Policy for details.
    :param versions_list: list of application directories containing version
    :param versions_path: this directory contains all the versions of the program
    :param pattern: the pattern of the name that contains version, e.g. "my_program_v{}"
    :return: the directory with the last version of the program
    :raises ValueError: if no valid version is found in the given input
    """
    version_dirs = available_versions(versions_path=versions_path, versions_list=versions_list, pattern=pattern)
    if not version_dirs:
        raise ValueError("no valid version found in the given input")
    sorted_versions = sort_versions(list(version_dirs.keys()))
    return version_dirs[sorted_versions[-1]]

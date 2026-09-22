"""Command-line interface for extract_version: extract, validate and sort versions embedded in strings.

Exit-code and output contract
-----------------------------
Every subcommand (``extract``, ``validate``, ``sort``, ``available``,
``last-version``) obeys the same three-way exit-code contract so callers and
scripts can distinguish outcomes without parsing stderr:

* ``0`` -- full success: the command produced its output for every input.
* ``1`` -- semantic failure or partial failure. A semantic failure means the
  request was well-formed but could not be satisfied: no version was found, a
  sort key was invalid, or a pattern declared the wrong number of capture
  groups / was an invalid regex. A partial failure means a multi-name call
  succeeded for some names and failed for others (see per-command notes below).
* ``2`` -- missing or invalid input: no names were given and stdin was empty or
  a TTY, i.e. an argument-usage problem rather than a semantic one. (argparse
  itself also exits ``2`` for unknown subcommands/flags.)

Output routing is uniform across commands: stdout carries success output only
(plain text, or JSON with ``--json``); stderr carries every diagnostic message.
On a pure semantic/usage failure (exit ``2``, or an exit ``1`` that produced no
successes) stdout is empty and the reason is on stderr.

Output-format contract
-----------------------
stdout has exactly three plain-text shapes, one per result kind:

* Scalar (``last-version``, and ``sort`` when it produced a single value): the
  value on a single line.
* List (``extract``, ``validate``, and ``sort``'s list output): one item per
  line, in the order the command produced them (``sort`` in version order,
  ``extract``/``validate`` in input order).
* Version-to-name mapping (``available``): one ``version\tname`` line per entry
  (tab-separated), ordered by the numeric version-sort contract of
  ``sort_versions()`` -- so ``1.9`` precedes ``1.10`` -- **not** lexicographically
  by string key.

``--json`` serializes the same logical content as the plain-text mode: a JSON
scalar, array, or object respectively. The mapping's JSON keys are emitted in
the same numeric version order as the plain-text lines (the dict is rebuilt in
sorted-key order before ``json.dumps``). Diagnostics are never mixed into either
stdout shape: each command only ever hands successful results to ``_print`` and
routes every message to stderr.

Partial-success stdout shape: for the per-name commands (``extract`` /
``validate``), stdout contains only the successfully-produced values; failed
inputs are reported solely on stderr and are never represented in-band on stdout
(no placeholder line, no error object inside the JSON array). Successes and
failures thus never share a stream even when both occur in one call.

Per-command stderr messaging
----------------------------
* ``extract`` / ``validate`` -- process each name independently. Successful
  results are printed to stdout and each failed name produces one stderr line
  (``no version found in <name>`` / ``invalid version <name>``); the command
  exits ``1`` if any name failed. This is deliberate partial-success behavior,
  explicitly NOT all-or-nothing: valid results are still emitted alongside the
  per-name failures. (A malformed ``--pattern`` is a different, whole-command
  failure: ``extract`` reports the pattern error on stderr and exits ``1``
  without flushing partial results.)
* ``sort`` -- all-or-nothing, per ``sort_versions()``'s own contract: a single
  entry that is not a valid version fails the whole sort with one stderr line
  and exit ``1`` (nothing is printed to stdout).
* ``available`` / ``last-version`` -- operate on the whole inventory as a unit
  rather than per name. A pattern/regex error, or an inventory that yields no
  valid version, exits ``1`` with a single stderr line describing the failure
  (``available`` also prints its empty result -- ``{}`` under ``--json`` -- to
  stdout in the empty-inventory case, whereas ``last-version`` prints nothing).
  A bad ``--path`` (nonexistent, not a directory, or permission-denied, i.e. an
  ``OSError`` from ``os.listdir()``) is likewise a whole-command failure: it
  exits ``1`` with a single friendly stderr line, never a raw Python traceback.
"""

import argparse
import json
import re
import sys

from extract_version.version_info import (
    PatternArityError,
    available_versions,
    extract_version,
    get_last_version,
    sort_versions,
    validate_version,
)


def _read_names(names):
    """
    Return the given positional names, or fall back to reading newline-separated
    names from stdin when none were given and stdin is piped.
    """
    if names:
        return names
    if not sys.stdin.isatty():
        return [line.strip() for line in sys.stdin if line.strip()]
    return []


def _print(value, as_json):
    if isinstance(value, dict):
        # Order mapping output by the library's numeric version-sort contract
        # (via the public sort_versions()), not lexicographically by string key,
        # so "1.9" precedes "1.10". Rebuild the dict in that key order so --json
        # serialization inherits the same ordering (dict/json.dumps preserve it).
        ordered = {version: value[version] for version in sort_versions(list(value.keys()))}
        if as_json:
            print(json.dumps(ordered))
        else:
            for version, name in ordered.items():
                print(f"{version}\t{name}")
        return
    if as_json:
        print(json.dumps(value))
        return
    if isinstance(value, list):
        for item in value:
            print(item)
    else:
        print(value)


def _cmd_extract(args):
    names = _read_names(args.names)
    if not names:
        print(
            "extract-version extract: no input given (pass NAME(s) or pipe them on stdin)",
            file=sys.stderr,
        )
        return 2

    results = []
    failed = False
    for name in names:
        try:
            version = extract_version(version_string=name, pattern=args.pattern)
        except (ValueError, re.error) as error:
            print(f"extract-version extract: {error}", file=sys.stderr)
            return 1
        if version:
            results.append(version)
        else:
            failed = True
            print(
                f"extract-version extract: no version found in {name!r}",
                file=sys.stderr,
            )

    _print(results, args.json)
    return 1 if failed else 0


def _cmd_validate(args):
    names = _read_names(args.names)
    if not names:
        print(
            "extract-version validate: no input given (pass NAME(s) or pipe them on stdin)",
            file=sys.stderr,
        )
        return 2

    results = []
    failed = False
    for name in names:
        version = validate_version(name)
        if version:
            results.append(version)
        else:
            failed = True
            print(f"extract-version validate: invalid version {name!r}", file=sys.stderr)

    _print(results, args.json)
    return 1 if failed else 0


def _cmd_sort(args):
    versions = _read_names(args.versions)
    if not versions:
        print(
            "extract-version sort: no input given (pass VERSION(s) or pipe them on stdin)",
            file=sys.stderr,
        )
        return 2

    try:
        sorted_versions = sort_versions(versions, descending=args.descending)
    except ValueError as error:
        print(f"extract-version sort: {error}", file=sys.stderr)
        return 1

    _print(sorted_versions, args.json)
    return 0


def _versions_source(args):
    """
    Build the versions_path/versions_list kwargs for available_versions()/get_last_version(),
    giving --path priority over positional/stdin names, matching the library's own precedence.
    """
    if args.path:
        return {"versions_path": args.path}
    names = _read_names(args.names)
    return {"versions_list": names} if names else None


def _cmd_available(args):
    source = _versions_source(args)
    if source is None:
        print(
            "extract-version available: no input given (pass NAME(s), --path, or pipe on stdin)",
            file=sys.stderr,
        )
        return 2

    try:
        versions = available_versions(pattern=args.pattern, **source)
    # OSError covers a bad --path: nonexistent (FileNotFoundError), not a
    # directory (NotADirectoryError), or permission-denied (PermissionError)
    # from os.listdir(). Report it as a friendly stderr message + exit 1 like
    # every other failure, never a raw traceback.
    except (ValueError, re.error, OSError) as error:
        print(f"extract-version available: {error}", file=sys.stderr)
        return 1

    _print(versions, args.json)
    return 0 if versions else 1


def _cmd_last_version(args):
    source = _versions_source(args)
    if source is None:
        print(
            "extract-version last-version: no input given (pass NAME(s), --path, or pipe on stdin)",
            file=sys.stderr,
        )
        return 2

    try:
        last_version = get_last_version(pattern=args.pattern, **source)
    # PatternArityError subclasses ValueError, so this must stay before the plain
    # except ValueError below (order determines which clause matches). OSError
    # (from a bad --path via os.listdir(): nonexistent, not a directory, or
    # permission-denied) is not a ValueError, so it is caught here and reported
    # as a friendly stderr message + exit 1 rather than a raw traceback.
    except (re.error, PatternArityError, OSError) as error:
        print(f"extract-version last-version: {error}", file=sys.stderr)
        return 1
    # Reaching here means available_versions() found no version. Its "either
    # versions_list or versions_path" ValueError can't reach the CLI because the
    # source is None guard above always supplies one of the two arguments; keep
    # that guard so this generic message stays accurate.
    except ValueError:
        print(
            "extract-version last-version: no version found in the given input",
            file=sys.stderr,
        )
        return 1

    _print(last_version, args.json)
    return 0


def _build_parser():
    parser = argparse.ArgumentParser(prog="extract-version", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    json_parser = argparse.ArgumentParser(add_help=False)
    json_parser.add_argument("--json", action="store_true", help="print output as JSON")

    pattern_parser = argparse.ArgumentParser(add_help=False)
    pattern_parser.add_argument(
        "--pattern",
        help="regex with one capture group locating the version, e.g. 'PyCharm-(.*)-linux'",
    )

    extract_parser = subparsers.add_parser(
        "extract",
        parents=[json_parser, pattern_parser],
        help="extract a version from a string or name",
    )
    extract_parser.add_argument("names", metavar="NAME", nargs="*")
    extract_parser.set_defaults(func=_cmd_extract)

    validate_parser = subparsers.add_parser(
        "validate",
        parents=[json_parser],
        help="check that a string is exactly a version",
    )
    validate_parser.add_argument("names", metavar="NAME", nargs="*")
    validate_parser.set_defaults(func=_cmd_validate)

    sort_parser = subparsers.add_parser("sort", parents=[json_parser], help="sort a list of version strings")
    sort_parser.add_argument("versions", metavar="VERSION", nargs="*")
    sort_parser.add_argument("--descending", action="store_true", help="sort from newest to oldest")
    sort_parser.set_defaults(func=_cmd_sort)

    available_parser = subparsers.add_parser(
        "available",
        parents=[json_parser, pattern_parser],
        help="map versions to the names they were found in",
    )
    available_parser.add_argument("names", metavar="NAME", nargs="*")
    available_parser.add_argument("--path", help="directory to scan instead of NAME arguments/stdin")
    available_parser.set_defaults(func=_cmd_available)

    last_version_parser = subparsers.add_parser(
        "last-version",
        parents=[json_parser, pattern_parser],
        help="print the name with the newest version",
    )
    last_version_parser.add_argument("names", metavar="NAME", nargs="*")
    last_version_parser.add_argument("--path", help="directory to scan instead of NAME arguments/stdin")
    last_version_parser.set_defaults(func=_cmd_last_version)

    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

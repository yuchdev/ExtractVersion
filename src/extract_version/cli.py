"""Command-line interface for extract_version: extract, validate and sort versions embedded in strings."""

import argparse
import json
import sys

from extract_version.version_info import (
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
    if as_json:
        print(json.dumps(value))
        return
    if isinstance(value, dict):
        for version, name in sorted(value.items(), key=lambda item: item[0]):
            print(f"{version}\t{name}")
    elif isinstance(value, list):
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
        version = extract_version(version_string=name, pattern=args.pattern)
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

    versions = available_versions(pattern=args.pattern, **source)
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
    except (IndexError, ValueError):
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

import os
import re
import tempfile
import unittest

from extract_version.version_info import (
    PatternArityError,
    available_versions,
    extract_version,
    get_last_version,
    sort_versions,
    validate_version,
)


class TestVersionPath(unittest.TestCase):
    def test_validate_version_valid(self):
        """
        Test validate version strings
        """
        valid_versions = ["0.87", "1.00", "2018.1.2"]
        for name in valid_versions:
            self.assertEqual(validate_version(version_string=name), name)

    def test_validate_version_invalid(self):
        """
        Test validate invalid version strings
        """
        valid_versions = ["0.", "00", "NoVersion"]
        for name in valid_versions:
            self.assertEqual(validate_version(version_string=name), "")

    def test_validate_version_supported_shapes(self):
        """
        Test that both supported shapes (X.Y and X.Y.Z), including leading
        zeros, validate to themselves
        """
        valid_versions = ["1.0", "2020.1.0", "0.01", "1.00", "01.02.03"]
        for name in valid_versions:
            self.assertEqual(validate_version(version_string=name), name)

    def test_validate_version_rejects_near_misses(self):
        """
        Test that near-misses and trailing/leading garbage are rejected by the
        exact (full-string) validation
        """
        near_misses = [
            "1.0beta",  # alphabetic suffix
            "v1.0",  # alphabetic prefix
            "1.0.0abc",  # trailing garbage after X.Y.Z
            "1.0.0-linux",  # trailing OS/build suffix after X.Y.Z
            "1.0.0 ",  # trailing space
            " 1.0.0",  # leading space
            "1.0.0.0",  # too many segments (trailing ".0")
            "1",  # bare single integer is not a version
            "1.",  # malformed dotted token
        ]
        for name in near_misses:
            self.assertEqual(validate_version(version_string=name), "")

    def test_extract_pattern_valid(self):
        """
        Test extract version from the string with known pattern
        """
        valid_strings = {
            "0.87": {"pattern": "(.*)", "expected": "0.87"},
            "1.00": {"pattern": "(.*)", "expected": "1.00"},
            "PyCharm-2018.1.2": {"pattern": "PyCharm-(.*)", "expected": "2018.1.2"},
            "PyCharm-2018.1.2-linux": {"pattern": "PyCharm-(.*)-linux", "expected": "2018.1.2"},
        }
        for name, data in valid_strings.items():
            extracted_version = extract_version(version_string=name, pattern=data["pattern"])
            expected_version = data["expected"]
            self.assertEqual(extracted_version, expected_version)

    def test_extract_pattern_invalid(self):
        """
        Test extract version from the string with known invalid pattern or invalid name
        """
        invalid_patterns = {
            # no version in name
            "ApplicationNoVersion": {"expected": ""},
            # pattern don't match
            "0.87": {"pattern": "x(.*)", "expected": ""},
            # pattern don't match
            "1.00": {"pattern": "(.*)x", "expected": ""},
            # name don't match
            "PyCharm-2018.1.2": {"pattern": "(.*)", "expected": ""},
        }
        for name, data in invalid_patterns.items():
            extracted_version = extract_version(
                version_string=name, pattern=data["pattern"] if "pattern" in data else None
            )
            expected_version = data["expected"]
            self.assertEqual(extracted_version, expected_version)

    def test_extract_no_pattern_valid(self):
        """
        Test extract version from the string without known pattern
        """
        valid_strings = {
            "0.87": {"expected": "0.87"},
            "1.00": {"expected": "1.00"},
            "PyCharm-2018.1.2": {"expected": "2018.1.2"},
            "PyCharm-2018.1.2-linux": {"expected": "2018.1.2"},
        }
        for name, data in valid_strings.items():
            extracted_version = extract_version(version_string=name)
            expected_version = data["expected"]
            self.assertEqual(extracted_version, expected_version)

    def test_extract_no_pattern_invalid(self):
        """
        Test extract version from the string without known pattern with invalid name
        """
        invalid_patterns = {
            # no version in name
            "ApplicationNoVersion": {"expected": ""},
            # version don't match
            "0.": {"expected": ""},
            # version don't match
            "x.00": {"expected": ""},
            # version don't match
            "PyCharm-2018.x.2": {"expected": ""},
        }
        for name, data in invalid_patterns.items():
            extracted_version = extract_version(version_string=name)
            expected_version = data["expected"]
            self.assertEqual(extracted_version, expected_version)

    def test_extract_no_pattern_supported_shapes(self):
        """
        Test extraction of each supported shape, with and without leading zeros
        and embedded in a larger string; the three-segment form wins over the
        two-segment fragment
        """
        valid_strings = {
            "1.0": "1.0",  # bare X.Y
            "2020.1.0": "2020.1.0",  # bare X.Y.Z (precedence over "2020.1")
            "0.01": "0.01",  # leading zeros preserved (X.Y)
            "01.02.03": "01.02.03",  # leading zeros preserved (X.Y.Z)
            "my_program_v1.0": "1.0",  # embedded X.Y
            "PyCharm-2020.1.0": "2020.1.0",  # embedded X.Y.Z
        }
        for name, expected in valid_strings.items():
            self.assertEqual(extract_version(version_string=name), expected)

    def test_extract_no_pattern_rejects_near_misses(self):
        """
        Test that strings without a valid version shape extract to ""
        """
        near_misses = ["v", "beta", "1", "1.", "NoVersion"]
        for name in near_misses:
            self.assertEqual(extract_version(version_string=name), "")

    def test_extract_no_pattern_precedence_multi_candidate(self):
        """
        Test that, with no pattern on a real multi-candidate string, the
        three-segment X.Y.Z shape wins over a two-segment X.Y fragment by
        specificity rather than by order of appearance in the string
        """
        multi_candidate_strings = {
            # X.Y.Z ("2018.1.2") wins over the trailing X.Y fragment ("10.0")
            "PyCharm-2018.1.2-windows-10.0": "2018.1.2",
            # X.Y ("10.0") appears first, yet the later X.Y.Z ("2.3.4") wins
            "10.0 and 2.3.4": "2.3.4",
        }
        for name, expected in multi_candidate_strings.items():
            self.assertEqual(extract_version(version_string=name), expected)

    def test_extract_no_pattern_same_shape_picks_first(self):
        """
        Test that, with no pattern and multiple candidates of the SAME shape,
        the first match in the string wins (current version[0] behavior). This
        pins the tie-break that specificity precedence cannot cover: two equally
        specific candidates are ordered only by position of appearance.
        """
        same_shape_strings = {
            # Two three-segment X.Y.Z candidates: the first one wins
            "1.0.0 and 2.0.0": "1.0.0",
            # Two two-segment X.Y candidates, no X.Y.Z: the first one wins
            "1.0 or 2.0": "1.0",
        }
        for name, expected in same_shape_strings.items():
            self.assertEqual(extract_version(version_string=name), expected)

    def test_extract_pattern_disambiguates_multi_candidate(self):
        """
        Test the module docstring's own disambiguation example: an explicit
        pattern selects the version out of a string that also holds a competing
        numeric group, and a pattern whose capture group is not a valid version
        shape extracts to ""
        """
        # Positive: docstring example 3 — pattern isolates the version
        self.assertEqual(
            extract_version(
                version_string="PyCharm-2018.1.2-windows-10.0",
                pattern="PyCharm-(.*)-windows-10.0",
            ),
            "2018.1.2",
        )
        # Negative: capture group grabs non-version text ("-windows-10.0")
        self.assertEqual(
            extract_version(
                version_string="PyCharm-2018.1.2-windows-10.0",
                pattern="PyCharm-2018.1.2(.*)",
            ),
            "",
        )

    def test_extract_pattern_no_match_returns_empty(self):
        """
        Test that a pattern which finds nothing in the string returns "" (this
        is "no version found", not a caller error)
        """
        self.assertEqual(
            extract_version(version_string="PyCharm-2018.1.2", pattern="Rider-(.*)"),
            "",
        )

    def test_extract_pattern_no_capture_group_raises_value_error(self):
        """
        Test that a pattern that matches but declares no capture group is a
        caller error and raises a descriptive PatternArityError (a ValueError
        subclass; intentional tightening from the previous bare IndexError out
        of match.group(1))
        """
        with self.assertRaises(PatternArityError) as context:
            extract_version(version_string="PyCharm-2018.1.2", pattern="PyCharm-.*")
        self.assertIn("capture group", str(context.exception))

    def test_extract_pattern_non_capturing_group_raises_value_error(self):
        """
        Test that a non-capturing group ``(?:...)`` (which yields zero capture
        groups) is a caller error and raises the same descriptive
        PatternArityError, locked in as a distinct case from the plain no-parens
        pattern
        """
        with self.assertRaises(PatternArityError) as context:
            extract_version(version_string="PyCharm-2018.1.2", pattern="PyCharm-(?:.*)")
        self.assertIn("capture group", str(context.exception))

    def test_extract_pattern_multiple_capture_groups_raises_value_error(self):
        """
        Test that a pattern with two or more capture groups is a caller error and
        raises a descriptive PatternArityError (intentional tightening: before
        the guard counted only zero groups, this silently returned
        match.group(1) -- "10.0" here -- and ignored the rest, contradicting
        "exactly one")
        """
        with self.assertRaises(PatternArityError) as context:
            extract_version(version_string="10.0-and-2.3.4", pattern="(10.0)-and-(2.3.4)")
        self.assertIn("capture group", str(context.exception))

    def test_extract_pattern_invalid_regex_raises_re_error(self):
        """
        Test that an invalid regular expression in the pattern raises re.error
        (the self-documenting exception is left to propagate, not masked to "")
        """
        with self.assertRaises(re.error):
            extract_version(version_string="PyCharm-2018.1.2", pattern="PyCharm-(")

    def test_extract_pattern_captured_but_invalid_returns_empty(self):
        """
        Test that a capture group grabbing non-version text routes through the
        same exact grammar gate as non-pattern extraction and returns "" (no
        pattern-path bypass of validation)
        """
        self.assertEqual(
            extract_version(version_string="PyCharm-abc", pattern="PyCharm-(.*)"),
            "",
        )

    def test_sort_versions(self):
        """
        Test sort versions
        """
        unsorted_versions = ["20", "1.0", "1.0.2", "1.0.1", "10"]
        expected_sorted_versions = ["1.0", "1.0.1", "1.0.2", "10", "20"]
        sorted_versions = sort_versions(unsorted_versions)
        self.assertEqual(sorted_versions, expected_sorted_versions)

    def test_sort_versions_mixed_shapes(self):
        """
        Test that two-segment (X.Y) and three-segment (X.Y.Z) shapes sort
        together numerically per segment, with missing trailing segments
        padded to zero
        """
        unsorted_versions = ["1.2.0", "1.0", "1.0.1", "1.2", "2.0.0"]
        expected_sorted_versions = ["1.0", "1.0.1", "1.2", "1.2.0", "2.0.0"]
        sorted_versions = sort_versions(unsorted_versions)
        self.assertEqual(sorted_versions, expected_sorted_versions)

    def test_sort_versions_equal_shapes_tie_break(self):
        """
        Test that "1.0" and "1.0.0" normalize to the same numeric key and are
        ordered deterministically by their original string (lexicographically),
        not by input order
        """
        # Input order deliberately puts the three-segment form first
        unsorted_versions = ["1.0.0", "1.0", "1.0.1"]
        # Padded tuples: "1.0" -> (1, 0, 0), "1.0.0" -> (1, 0, 0) tie, then
        # broken by string ("1.0" < "1.0.0"); "1.0.1" -> (1, 0, 1) is last
        expected_sorted_versions = ["1.0", "1.0.0", "1.0.1"]
        sorted_versions = sort_versions(unsorted_versions)
        self.assertEqual(sorted_versions, expected_sorted_versions)

    def test_sort_versions_leading_zero_numeric_equality(self):
        """
        Test that leading zeros are numerically equal under sort_versions
        (int("00") == int("0")), so "1.00" and "1.0" tie and the tie is broken
        deterministically by the original string
        """
        unsorted_versions = ["1.00", "1.0.1", "1.0"]
        # "1.0" -> (1, 0, 0) and "1.00" -> (1, 0, 0) tie; string tie-break
        # orders "1.0" before "1.00"; "1.0.1" -> (1, 0, 1) is last
        expected_sorted_versions = ["1.0", "1.00", "1.0.1"]
        sorted_versions = sort_versions(unsorted_versions)
        self.assertEqual(sorted_versions, expected_sorted_versions)

    def test_sort_versions_descending(self):
        """
        Test that descending=True reverses the ordering
        """
        unsorted_versions = ["1.0", "1.0.2", "1.0.1", "2.0"]
        expected_sorted_versions = ["2.0", "1.0.2", "1.0.1", "1.0"]
        sorted_versions = sort_versions(unsorted_versions, descending=True)
        self.assertEqual(sorted_versions, expected_sorted_versions)

    def test_available_versions(self):
        """
        Test all available versions of application
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_version_dirs = {
            "test_data/versions/cellar": {
                "pattern": "(.*)",
                "expected": {"0.01": "0.01", "1.0": "1.0", "0.87": "0.87"},
            },
            "test_data/versions/pycharm": {
                "pattern": "PyCharm(.*)",
                "expected": {"2020.3": "PyCharm2020.3", "2021.1": "PyCharm2021.1", "2020.1": "PyCharm2020.1"},
            },
        }
        for versions_path, data in test_version_dirs.items():
            full_versions_path = os.path.join(current_dir, versions_path)
            all_versions = available_versions(versions_path=full_versions_path, pattern=data["pattern"])
            expected_all_versions = data["expected"]
            self.assertEqual(all_versions, expected_all_versions)

    def test_get_last_version(self):
        """
        Test last version directory
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_version_dirs = {
            "test_data/versions/cellar": {"pattern": "(.*)", "expected": "1.0"},
            "test_data/versions/pycharm": {"pattern": "PyCharm(.*)", "expected": "PyCharm2021.1"},
        }
        for versions_path, data in test_version_dirs.items():
            full_versions_path = os.path.join(current_dir, versions_path)
            last_version = get_last_version(versions_list=os.listdir(full_versions_path), pattern=data["pattern"])
            expected_last_version_dir = data["expected"]
            self.assertEqual(last_version, expected_last_version_dir)

    def test_available_versions_filters_unparseable(self):
        """
        Test that available_versions() filters out names whose version cannot be
        extracted instead of collapsing them onto a single "" key (intentional
        tightening: no blank key, entry count reflects only valid versions)
        """
        names = ["1.0", "NoVersion", "PyCharm-2020.1.0", "beta", "1"]
        result = available_versions(versions_list=names)
        self.assertEqual(result, {"1.0": "1.0", "2020.1.0": "PyCharm-2020.1.0"})
        self.assertNotIn("", result)
        self.assertEqual(len(result), 2)

    def test_available_versions_all_unparseable_is_empty(self):
        """
        Test that an inventory in which no name yields a version maps to an empty
        dict (no "" key), rather than a one-entry {"": ...} mapping
        """
        result = available_versions(versions_list=["NoVersion", "beta", "1"])
        self.assertEqual(result, {})

    def test_available_versions_from_path_filters_unparseable(self):
        """
        Test that the versions_path (os.listdir) source applies the same
        invalid-entry filtering as the versions_list source: a directory holding
        both valid version-named entries and non-version names ("NoVersion",
        "latest") yields only the valid ones, with no "" key leaking in
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mixed_path = os.path.join(current_dir, "test_data/versions/mixed")
        result = available_versions(versions_path=mixed_path)
        self.assertEqual(result, {"1.0": "1.0", "2.0.0": "2.0.0"})
        self.assertNotIn("", result)
        # get_last_version over the same filesystem source returns the newest
        # valid entry, ignoring the unparseable directory names entirely
        self.assertEqual(get_last_version(versions_path=mixed_path), "2.0.0")

    def test_available_versions_from_path_all_unparseable_is_empty(self):
        """
        Test the filesystem-source parity of the all-invalid boundary already
        pinned for the list source: a directory in which no entry yields a
        version maps to an empty dict via available_versions() and makes
        get_last_version() raise a descriptive ValueError, so a mutation that
        filtered differently (or crashed) on an all-invalid os.listdir() result
        would be caught here too
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        all_invalid_path = os.path.join(current_dir, "test_data/versions/all-invalid")
        self.assertEqual(available_versions(versions_path=all_invalid_path), {})
        with self.assertRaises(ValueError) as context:
            get_last_version(versions_path=all_invalid_path)
        self.assertIn("no valid version found", str(context.exception))

    def test_get_last_version_from_path_returns_original_dir_name(self):
        """
        Test that the filtering versions_path source returns the original
        directory name, not the normalized version key: this fixture mixes
        unparseable names with valid entries whose directory names differ from
        their extracted versions ("app-1.0" -> "1.0", "app-2.0.0" -> "2.0.0"),
        so a mutation returning the sorted version key ("2.0.0") instead of the
        winning directory name ("app-2.0.0") is caught here
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filtered_path = os.path.join(current_dir, "test_data/versions/filtered")
        self.assertEqual(
            available_versions(versions_path=filtered_path),
            {"1.0": "app-1.0", "2.0.0": "app-2.0.0"},
        )
        self.assertEqual(get_last_version(versions_path=filtered_path), "app-2.0.0")

    def test_get_last_version_empty_raises_value_error(self):
        """
        Test that get_last_version() raises a descriptive ValueError on an empty
        inventory (intentional tightening from the previous bare IndexError)
        """
        with self.assertRaises(ValueError) as context:
            get_last_version(versions_list=[])
        self.assertIn("no valid version found", str(context.exception))

    def test_get_last_version_all_unparseable_raises_value_error(self):
        """
        Test that get_last_version() raises a descriptive ValueError when every
        inventory entry is unparseable (would previously crash on int("") or an
        empty-list index)
        """
        with self.assertRaises(ValueError) as context:
            get_last_version(versions_list=["NoVersion", "beta", "1"])
        self.assertIn("no valid version found", str(context.exception))

    def test_get_last_version_ignores_unparseable_entries(self):
        """
        Test that get_last_version() returns the newest valid entry while simply
        ignoring unparseable names mixed into the inventory
        """
        names = ["NoVersion", "1.0", "2.0.0", "beta", "1.5"]
        self.assertEqual(get_last_version(versions_list=names), "2.0.0")

    def test_extract_validate_sort_consistency(self):
        """
        Test cross-function consistency for the shared parse helper: every
        candidate that extract_version() accepts from a bare string is also
        accepted verbatim by validate_version() and survives a round-trip
        through sort_versions() as a valid, single-element sort
        """
        candidates = ["1.0", "2020.1.0", "0.01", "01.02.03", "1.00"]
        for candidate in candidates:
            extracted = extract_version(version_string=candidate)
            self.assertEqual(extracted, candidate)
            self.assertEqual(validate_version(version_string=extracted), candidate)
            self.assertEqual(sort_versions([extracted]), [candidate])

    def test_extract_embedded_then_validate_and_sort_consistency(self):
        """
        Test that a version extracted from a larger string (embedded and
        multi-candidate cases) is itself a standalone-valid version and sorts
        into the expected order alongside its peers, proving extraction,
        validation, and sorting share one grammar
        """
        embedded = {
            "my_program_v1.0": "1.0",
            "PyCharm-2020.1.0": "2020.1.0",
            "PyCharm-2018.1.2-windows-10.0": "2018.1.2",
        }
        extracted_versions = []
        for name, expected in embedded.items():
            extracted = extract_version(version_string=name)
            self.assertEqual(extracted, expected)
            # The extracted fragment must itself pass standalone validation
            self.assertEqual(validate_version(version_string=extracted), expected)
            extracted_versions.append(extracted)
        # All extracted versions sort consistently by their shared numeric key
        self.assertEqual(
            sort_versions(list(extracted_versions)),
            ["1.0", "2018.1.2", "2020.1.0"],
        )

    def test_validate_rejected_candidate_not_extracted(self):
        """
        Test the negative side of cross-function consistency: candidates the
        shared grammar gate rejects are neither validated nor extracted as
        standalone versions (bare integers and trailing-garbage near-misses)
        """
        rejected = ["1", "1.0.0abc", "v1.0", "1."]
        for candidate in rejected:
            self.assertEqual(validate_version(version_string=candidate), "")
            self.assertEqual(extract_version(version_string=candidate, pattern="(.*)"), "")

    def test_sort_accepts_bare_single_segment_validate_rejects(self):
        """
        Test the two-layer split's core design intent purely through public
        functions: the permissive sort layer accepts bare single-segment values
        like "1" and "2020" (padding them to a numeric key and ordering them
        against normal shapes), while the grammar-gated validation layer rejects
        those same bare integers as non-versions. This pins the divergence the
        former private _normalize_key-vs-_parse_version tests asserted, without
        reaching into private helpers.
        """
        # Permissive layer: bare single-segment values sort against real shapes
        # (padded to (1, 0, 0) and (2020, 0, 0) respectively).
        self.assertEqual(
            sort_versions(["2020", "1.0.1", "1", "1.0"]),
            ["1", "1.0", "1.0.1", "2020"],
        )
        # Grammar-gated layer: the same bare integers are not valid versions.
        self.assertEqual(validate_version(version_string="1"), "")
        self.assertEqual(validate_version(version_string="2020"), "")

    def test_sort_versions_four_segment_untruncated(self):
        """
        Test and pin today's behavior for a 4+ segment input mixed with normal
        shapes: sort_versions() does NOT truncate to three segments, it compares
        the full un-padded tuple, so "1.2.3.4" sorts by all four segments and
        falls between "1.2.3" ((1, 2, 3)) and "1.2.4" ((1, 2, 4, 0)).
        """
        unsorted_versions = ["1.2.4", "1.2.3.4", "1.2.3"]
        expected_sorted_versions = ["1.2.3", "1.2.3.4", "1.2.4"]
        self.assertEqual(sort_versions(unsorted_versions), expected_sorted_versions)

    def test_sort_versions_non_numeric_segment_raises_value_error(self):
        """
        Test that the permissive sort layer trusts its input (no grammar gate):
        a non-numeric segment such as "1.x" reaches int() and raises ValueError.
        This documents that sort_versions() must be fed already-valid versions;
        it does not silently filter or reject malformed entries.
        """
        with self.assertRaises(ValueError):
            sort_versions(["1.x", "1.0"])

    def test_duplicate_normalized_winner_stable_across_sources(self):
        """
        Test the Compatibility Policy stance on duplicate normalized versions:
        when two entries normalize to the same key ("1.0" and "1.0.0" both pad
        to (1, 0, 0)), the winner is a pure function of the version strings and
        is identical whether sourced via versions_list or via versions_path
        (os.listdir())
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        duplicates_path = os.path.join(current_dir, "test_data/versions/duplicates")
        from_path = get_last_version(versions_path=duplicates_path)
        from_list = get_last_version(versions_list=os.listdir(duplicates_path))
        self.assertEqual(from_path, from_list)
        # "1.0" and "1.0.0" tie on (1, 0, 0); string tie-break makes "1.0.0" win
        self.assertEqual(from_path, "1.0.0")

    def test_versions_path_wins_over_versions_list(self):
        """
        Test the documented precedence rule: when both versions_path and
        versions_list are passed, versions_path (os.listdir) wins and the
        versions_list argument is ignored entirely -- the result reflects the
        fixture directory's contents, never the "9.9.9" sentinel or a merge of
        the two sources. This pins a mutation-survivable gap (a mutation that
        merged both inputs, or preferred versions_list, would be caught here).
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cellar_path = os.path.join(current_dir, "test_data/versions/cellar")
        # available_versions(): both sources supplied, path wins.
        result = available_versions(
            versions_path=cellar_path,
            versions_list=["9.9.9"],
            pattern="(.*)",
        )
        self.assertEqual(result, {"0.01": "0.01", "0.87": "0.87", "1.0": "1.0"})
        self.assertNotIn("9.9.9", result)
        # get_last_version(): same precedence, newest entry from the directory,
        # not the ignored "9.9.9" sentinel from versions_list.
        last_version = get_last_version(
            versions_path=cellar_path,
            versions_list=["9.9.9"],
            pattern="(.*)",
        )
        self.assertEqual(last_version, "1.0")

    def test_empty_versions_path_wins_over_versions_list(self):
        """
        Test that the precedence rule is unconditional: an EMPTY versions_path
        still wins over a non-empty versions_list, rather than silently falling
        back to the list. available_versions() must return {} and
        get_last_version() must raise its descriptive ValueError, proving the
        list data is never consulted once a path is given. Uses a temp dir
        because git cannot track an empty fixture directory.
        """
        with tempfile.TemporaryDirectory() as empty_path:
            self.assertEqual(
                available_versions(versions_path=empty_path, versions_list=["9.9.9"]),
                {},
            )
            with self.assertRaises(ValueError) as context:
                get_last_version(versions_path=empty_path, versions_list=["9.9.9"])
            self.assertIn("no valid version found", str(context.exception))

    def test_no_inventory_source_raises_value_error(self):
        """
        Test that calling available_versions() or get_last_version() with neither
        versions_list nor versions_path raises a descriptive ValueError rather
        than leaking a bare TypeError from iterating a None versions_list. This
        matches the module's precedent of documented, self-describing errors over
        incidental Python built-ins.
        """
        with self.assertRaises(ValueError) as available_context:
            available_versions()
        self.assertIn("versions_list or versions_path", str(available_context.exception))
        with self.assertRaises(ValueError) as last_context:
            get_last_version()
        self.assertIn("versions_list or versions_path", str(last_context.exception))

    def test_duplicate_normalized_winner_independent_of_list_order(self):
        """
        Test that the duplicate-normalized-version tie-break ("1.0" vs "1.0.0"
        -> "1.0.0" wins) is decided by the string tie-break in sort_versions(),
        not by input list order. Feeding a plain hand-written list in both
        orders must yield the same winner, complementing the filesystem-sourced
        stability check which is itself only filesystem-ordered.
        """
        self.assertEqual(get_last_version(versions_list=["1.0", "1.0.0"]), "1.0.0")
        self.assertEqual(get_last_version(versions_list=["1.0.0", "1.0"]), "1.0.0")


if __name__ == "__main__":
    unittest.main()

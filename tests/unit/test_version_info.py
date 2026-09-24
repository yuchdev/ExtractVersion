import os
import re
import unittest

from extract_version.version_info import (
    PatternArityError,
    available_versions,
    extract_version,
    get_last_version,
    sort_versions,
    validate_version,
)


class TestVersionInfoUnit(unittest.TestCase):
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

    def test_sort_versions_non_list_raises_assertion_error(self):
        """
        Test the second, structurally distinct failure mode of sort_versions
        (the first being a non-numeric segment): the ``assert isinstance(...,
        list)`` guard rejects a non-list argument (here a bare string, which is
        iterable and would otherwise be silently sorted character-by-character)
        with AssertionError rather than producing a nonsense per-character sort.
        """
        with self.assertRaises(AssertionError):
            sort_versions("1.0")

    def test_sort_versions_empty_segment_raises_value_error(self):
        """
        Test the boundary between a malformed-but-numeric-looking token and a
        truly non-numeric one: a trailing-dot entry like "1." splits to an
        EMPTY segment, so int("") raises ValueError inside _normalize_key. This
        is a distinct failure path from the "1.x" alphabetic-segment case and
        pins that sort_versions() does not silently treat "" as zero.
        """
        with self.assertRaises(ValueError):
            sort_versions(["1.", "1.0"])

    def test_extract_no_pattern_four_segment_matches_three_prefix(self):
        """
        Test the embedded-matching boundary for an over-long dotted run: with no
        pattern, extract_version() reads "1.2.3" out of "1.2.3.4" (REG_V1's
        three-segment match consumes the first three segments and stops), rather
        than returning "" or the full four-segment string. Pins that a 4+ segment
        input is treated as an embedded X.Y.Z, consistent with findall semantics,
        even though validate_version() rejects the same string as a whole.
        """
        self.assertEqual(extract_version(version_string="1.2.3.4"), "1.2.3")
        self.assertEqual(validate_version(version_string="1.2.3.4"), "")

    def test_available_versions_pattern_arity_error_propagates(self):
        """
        Test that a malformed --pattern (zero capture groups) is not swallowed by
        available_versions(): the PatternArityError raised inside extract_version
        propagates out unchanged, which is exactly what the CLI's available/
        last-version commands rely on to report a friendly pattern error instead
        of silently returning an empty inventory.
        """
        with self.assertRaises(PatternArityError):
            available_versions(versions_list=["PyCharm-2020.1.0"], pattern="PyCharm-.*")

    def test_available_versions_bad_path_raises_oserror(self):
        """
        Test the filesystem failure mode at the library level: a nonexistent
        versions_path lets os.listdir()'s FileNotFoundError (an OSError subclass)
        propagate, rather than being masked into an empty dict. This is the raw
        error the CLI later catches and reformats into a friendly message.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        missing_path = os.path.join(current_dir, "test_data/versions/no-such-dir-xyz")
        with self.assertRaises(OSError):
            available_versions(versions_path=missing_path)

    def test_get_last_version_pattern_arity_error_propagates(self):
        """
        Test that get_last_version() also lets a PatternArityError from a
        malformed --pattern propagate (a distinct failure from the "no valid
        version found" ValueError), so the CLI can distinguish a pattern-usage
        error from an empty inventory in its except clauses.
        """
        with self.assertRaises(PatternArityError):
            get_last_version(versions_list=["PyCharm-2020.1.0"], pattern="PyCharm-.*")


if __name__ == "__main__":
    unittest.main()

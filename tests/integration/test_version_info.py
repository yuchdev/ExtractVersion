import unittest

from extract_version.version_info import (
    available_versions,
    extract_version,
    get_last_version,
    sort_versions,
    validate_version,
)


class TestVersionInfoConsistency(unittest.TestCase):
    """
    Cross-function consistency between extract_version(), validate_version(),
    sort_versions(), and available_versions()/get_last_version() -- each test exercises more
    than one public function together.
    """

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


if __name__ == "__main__":
    unittest.main()

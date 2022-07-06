import os
import unittest
from extract_version.version_info import validate_version, extract_version, sort_versions
from extract_version.version_info import get_last_version, available_versions


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

    def test_extract_pattern_valid(self):
        """
        Test extract version from the string with known pattern
        """
        valid_strings = {
            "0.87": {
                "pattern": "(.*)",
                "expected": "0.87"
            },
            "1.00": {
                "pattern": "(.*)",
                "expected": "1.00"
            },
            "PyCharm-2018.1.2": {
                "pattern": "PyCharm-(.*)",
                "expected": "2018.1.2"
            },
            "PyCharm-2018.1.2-linux": {
                "pattern": "PyCharm-(.*)-linux",
                "expected": "2018.1.2"
            }
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
            "ApplicationNoVersion": {
                "expected": ""
            },
            # pattern don't match
            "0.87": {
                "pattern": "x(.*)",
                "expected": ""
            },
            # pattern don't match
            "1.00": {
                "pattern": "(.*)x",
                "expected": ""
            },
            # name don't match
            "PyCharm-2018.1.2": {
                "pattern": "(.*)",
                "expected": ""
            }
        }
        for name, data in invalid_patterns.items():
            extracted_version = extract_version(version_string=name,
                                                pattern=data["pattern"] if "pattern" in data else None)
            expected_version = data["expected"]
            self.assertEqual(extracted_version, expected_version)

    def test_extract_no_pattern_valid(self):
        """
        Test extract version from the string without known pattern
        """
        valid_strings = {
            "0.87": {
                "expected": "0.87"
            },
            "1.00": {
                "expected": "1.00"
            },
            "PyCharm-2018.1.2": {
                "expected": "2018.1.2"
            },
            "PyCharm-2018.1.2-linux": {
                "expected": "2018.1.2"
            }
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
            "ApplicationNoVersion": {
                "expected": ""
            },
            # version don't match
            "0.": {
                "expected": ""
            },
            # version don't match
            "x.00": {
                "expected": ""
            },
            # version don't match
            "PyCharm-2018.x.2": {
                "expected": ""
            }
        }
        for name, data in invalid_patterns.items():
            extracted_version = extract_version(version_string=name)
            expected_version = data["expected"]
            self.assertEqual(extracted_version, expected_version)

    def test_sort_versions(self):
        """
        Test sort versions
        """
        unsorted_versions = ["20", "1.0", "1.0.2", "1.0.1", "10"]
        expected_sorted_versions = ["1.0", "1.0.1", "1.0.2", "10", "20"]
        sorted_versions = sort_versions(unsorted_versions)
        self.assertEqual(sorted_versions, expected_sorted_versions)

    def test_available_versions(self):
        """
        Test all available versions of application
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_version_dirs = {
            "test_data/versions/cellar": {
                "pattern": "(.*)",
                "expected": {
                    '0.01': '0.01',
                    '1.0': '1.0',
                    '0.87': '0.87'
                }
            },
            "test_data/versions/pycharm": {
                "pattern": "PyCharm(.*)",
                "expected": {
                    '2020.3': 'PyCharm2020.3',
                    '2021.1': 'PyCharm2021.1',
                    '2020.1': 'PyCharm2020.1'
                }
            }
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
            "test_data/versions/cellar": {
                "pattern": "(.*)",
                "expected": "1.0"

            },
            "test_data/versions/pycharm": {
                "pattern": "PyCharm(.*)",
                "expected": "PyCharm2021.1"
            }
        }
        for versions_path, data in test_version_dirs.items():
            full_versions_path = os.path.join(current_dir, versions_path)
            last_version = get_last_version(versions_list=os.listdir(full_versions_path), pattern=data["pattern"])
            expected_last_version_dir = data["expected"]
            self.assertEqual(last_version, expected_last_version_dir)


if __name__ == "__main__":
    unittest.main()

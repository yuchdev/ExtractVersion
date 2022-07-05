import sys
from extract_version.extract_version import validate_version, extract_version


def main():

    pycharm_dir = "PyCharm-2018.1.2-linux"
    my_project_dir = "my_program_v1.0"
    print(f"Version of {pycharm_dir} is {extract_version(version_string=pycharm_dir)}")
    print(f"Version of {my_project_dir} is {extract_version(version_string=my_project_dir)}")

    valid_versions = ["0.87", "1.00", "2018.1.2"]
    invalid_versions = ["0.", "00", "NoVersion"]
    print(f"Valid versions: {[validate_version(item) for item in valid_versions]}")
    print(f"Invalid versions are erased: {[validate_version(item) for item in invalid_versions]}")

    return 0


if __name__ == '__main__':
    sys.exit(main())

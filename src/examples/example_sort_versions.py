import sys
from extract_version.version_info import sort_versions


def main():

    available_versions = ["2018.1.2", "2018.2.0", "2020.1.0"]
    print(f"Sort versions: {available_versions} -> {sort_versions(available_versions)}")
    print(f"Sort versions descending: {available_versions} -> {sort_versions(available_versions, descending=True)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

import sys
from extract_version.extract_version import sort_versions


def main():

    available_versions = ["PyCharm-2018.1.2", "PyCharm-2018.2.0", "PyCharm-2020.1.0"]
    print(f"Sort versions: {available_versions} -> {sort_versions(available_versions)}")
    print(f"Sort versions descending: {available_versions} -> {sort_versions(available_versions, descending=True)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

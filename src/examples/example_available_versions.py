import sys
import asyncio


def main():
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
    all_versions = available_versions(versions_path=full_versions_path, pattern=data["pattern"])
    print(all_versions)

    return 0


if __name__ == '__main__':
    sys.exit(main())

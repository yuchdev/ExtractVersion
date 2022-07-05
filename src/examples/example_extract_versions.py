import sys
import asyncio


def main():
    print(extract_version(version_string="PyCharm-2020.1.0"))
    print(extract_version(version_string="my_program_v1.0"))
    return 0


if __name__ == '__main__':
    sys.exit(main())

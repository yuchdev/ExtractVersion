import re
import os

__doc__ = """The module offers following functionality:
* Fetching version string from the string or name of the directory
* Validating version string
* Sorting config and application directories that contain versions in its name

Examples:
1. We fetch version "2020.1.0" from string "PyCharm-2020.1.0", or version "1.0" from "my_program_v1.0".
extract_version(version_string="PyCharm-2020.1.0")
> "2020.1.0"
extract_version(version_string="my_program_v1.0")
> "1.0"

2. Versions of PyCharm are named like ["PyCharm-2020.1.0", "PyCharm-2018.2.0", "PyCharm-2018.1.2"]
should be sorted like ["PyCharm-2018.1.2", "PyCharm-2018.2.0", "PyCharm-2020.1.0"]
sort_versions(["PyCharm-2018.1.2", "PyCharm-2018.2.0", "PyCharm-2020.1.0"])
> ["PyCharm-2018.1.2", "PyCharm-2018.2.0", "PyCharm-2020.1.0"]

3. In edge cases with more than one pattern, e.g. "PyCharm-2018.1.2-windows-10.0", 
we should provide a clue where the version should be extracted from, 
in a form of a regex-pattern, like "PyCharm-(.*)-windows-10.0".
Call of such function should look like:
extract_version(version_string='PyCharm-2018.1.2-windows-10.0', pattern='PyCharm-(.*)-windows-10.0')
> "2018.1.2"
"""

REG_V1 = re.compile(r'\d+\.\d+\.\d+')
REG_V2 = re.compile(r'\d+\.\d+')


def validate_version(version_string):
    """
    Validate version string
    :param version_string: exact version string, e.g. "1.0.0", "1.0"
    :return: version string if valid, "" otherwise
    """
    return version_string if REG_V1.match(version_string) or REG_V2.match(version_string) else ""


def sort_versions(versions_list, descending=False):
    """
    Accept list of versions looks like ['1.0.0', '1.0', '2']
    If minor version is missing, assume it is 0
    """
    assert isinstance(versions_list, list)
    versions_list.sort(key=lambda x: [int(y) for y in x.split('.')], reverse=descending)
    return versions_list


def extract_version(*, version_string, pattern=None):
    """
    Extract version from the string with or without known pattern
    Find in string either version of kind "1.0.0", "1.0" or "1"
    :param version_string: string containing the version, e.g. "PyCharm-2018.1.2-linux", "my_program_v1.0"
    :param pattern: the exact regex of the name that contains version, e.g. "PyCharm-(.*)-linux"
    """
    if pattern is not None:
        match = re.search(pattern, version_string)
        return validate_version(match.group(1)) if match is not None else ""

    if version := REG_V1.findall(version_string):
        return version[0]
    elif version := REG_V2.findall(version_string):
        return version[0]
    else:
        return ""


def available_versions(*, versions_list=None, versions_path=None, pattern=None):
    """
    All available versions of the program
    :param versions_list: list of application directories containing version
    :param versions_path: this directory contains all the versions of the program
    :param pattern: the pattern of the name that contains version, e.g. "my_program_v{}"
    :return: dictionary of pairs (version, path)
    """
    if versions_path is not None:
        versions_list = os.listdir(versions_path)
    version_dirs = {
        extract_version(version_string=dir_name, pattern=pattern): dir_name for dir_name in versions_list
    }
    return version_dirs


def get_last_version(*, versions_list=None, versions_path=None, pattern=None):
    """
    Get the last version of the program.
    Able to accept list of versions or path to the directory with versions,
    in the latter case the path has priority over list
    :param versions_list: list of application directories containing version
    :param versions_path: this directory contains all the versions of the program
    :param pattern: the pattern of the name that contains version, e.g. "my_program_v{}"
    :return: the directory with the last version of the program
    """
    version_dirs = available_versions(versions_path=versions_path, versions_list=versions_list, pattern=pattern)
    sorted_versions = sort_versions(list(version_dirs.keys()))
    return version_dirs[sorted_versions[-1]]

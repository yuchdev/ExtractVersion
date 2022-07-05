import os
import sys
import platform
import getpass
from pathlib import Path

__doc__ = """Execute IDEA dictionaries synchronization.
Applicable to all IDEA-like projects (PyCharm, WebStorm etc).
Could be implemented as a pre-commit hook.
"""
PYTHON = "python3"


def is_linux():
    """
    :return: True if system is Linux, False otherwise
    """
    return platform.system() == 'Linux'


def is_macos():
    """
    :return: True if system is macOS, False otherwise
    """
    return platform.system() == 'Darwin'


def is_windows():
    """
    :return: True if system is Windows, False otherwise
    """
    return platform.system() == 'Windows'


if is_macos() or is_linux():
    PYTHON = "python3"
elif is_windows():
    PYTHON = "python"


# merge_command += " ".join([merge_command + (" --idea-dictionary %s" % d) for d in dictionaries])
def environment_value(environment_name):
    """
    :param environment_name: Name of the environment variable
    :return: Value of the environment variable or the empty string if not exists
    """
    try:
        return os.environ[environment_name]
    except KeyError:
        return ''


def platform_system():
    """
    :return: 
    """
    return platform.system()


def files_with_compare(root_folder, file_name):
    """
    :param root_folder: Directory root project, where from we start looking for dictionaries
    :param file_name: Dictionary file name (should be the same for all IDEA projects)
    :return: List of paths to all dictionaries, including file name
    """
    dictionaries = []
    print("Look for %s in %s" % (file_name, root_folder))
    for path in Path(root_folder).rglob(file_name):
        dictionaries.append(str(path))
    return dictionaries


def debug_exit():
    """
    Interrupt the script for debug purposes
    """
    sys.exit(0)


def get_username():
    """
    Username in several attempts
    """
    if os.environ.get('USER'):
        return os.environ.get('USER')
    elif os.environ.get('USERNAME'):
        return os.environ.get('USERNAME')
    elif getpass.getuser():
        return getpass.getuser()
    elif os.path.basename(os.path.expanduser('~')):
        return os.path.basename(os.path.expanduser('~'))
    else:
        return 'atatat'


def main():
    """
    Execute IDEA dictionaries synchronization as a pre-commit hook.
    Applicable to all IDEA-like projects (PyCharm, WebStorm etc)
    :return: System return code
    """
    projects_dir = environment_value("PROJECTS")
    appdata_dir = environment_value("APPDATA")
    idea_user_dictionary = f"{get_username()}.xml"

    print(f"IDEA dictionary name {idea_user_dictionary}")

    if 0 == len(projects_dir):
        print("Environment variable PROJECTS is not found, exiting hook")
        sys.exit(0)

    print("Environment variable PROJECTS=%s" % projects_dir)

    dictionaries_project = os.path.join(projects_dir, "HomeDir/Scripting/dictionaries")
    if not os.path.isdir(dictionaries_project):
        print("Personal IDEA dictionary directory is not found, exiting hook")
        sys.exit(0)

    print("Personal IDEA dictionary location %s" % dictionaries_project)

    python_script = os.path.join(dictionaries_project, "dictionary_merge.py")
    personal_idea_dict = os.path.join(dictionaries_project, f"idea/{idea_user_dictionary}")
    personal_vassist_dict = os.path.join(dictionaries_project, "vassist/Dict/UserWords.txt")

    if not os.path.isfile(python_script):
        print("Python dictionary merge script is not found, exiting hook")
        sys.exit(0)

    if not os.path.isfile(personal_vassist_dict) or not os.path.isfile(personal_idea_dict):
        print("Python dictionary file is not found, exiting hook")
        sys.exit(0)

    idea_dictionaries = files_with_compare(projects_dir, idea_user_dictionary)
    vassist_dictionaries = files_with_compare(appdata_dir, "UserWords.txt")
    print("Found following dictionaries: {}".format(idea_dictionaries))
    if len(idea_dictionaries) + 1 < 2:
        print("Only %d dictionaries has been found, nothing to merge" % len(idea_dictionaries))
        return 0

    merge_command = "%s %s --vassist-dict %s" % (PYTHON, python_script, personal_vassist_dict)

    for dictionary in idea_dictionaries:
        merge_command = merge_command + (" --idea-dictionary %s" % dictionary)
    for dictionary in vassist_dictionaries:
        merge_command = merge_command + (" --vassist-dictionary %s" % dictionary)

    return os.system(merge_command)


###########################################################################
if __name__ == '__main__':
    sys.exit(main())

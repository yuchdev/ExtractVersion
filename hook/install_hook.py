import os
import sys
import stat
import platform


PYTHON = "python3"
HOOK_CONTENT = """#!/bin/sh
#
# This file should be located in '.git/hooks' directory
# Python version depends on system, on Linux/Mac it could be 'python3'
{python_bin} {hook_script}

"""


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


def create_commit_hook():
    """
    Create file 'pre-commit' in directory '.git/hooks'
    :return: system return code
    """
    print("Normally 'hook_dict.py' is located in the same directory as this script install_hook.py")
    current_dir = os.path.abspath(os.path.dirname(__file__))
    hook_dict_py = os.path.join(current_dir, 'hook_dict.py')

    if not os.path.isfile(hook_dict_py):
        print("File 'hook_dict.py' not found")
        sys.exit(1)
    git_dir = os.path.abspath('../.git/hooks')
    if not os.path.isdir(git_dir):
        print("Directory '.git/hooks' not found")
        sys.exit(1)
    pre_commit_path = os.path.join(git_dir, 'pre-commit')
    with open(pre_commit_path, 'w') as pre_commit:
        pre_commit.write(HOOK_CONTENT.format(python_bin=PYTHON, hook_script=hook_dict_py))
    if is_linux() or is_macos():
        st = os.stat(pre_commit_path)
        os.chmod(pre_commit_path, st.st_mode | stat.S_IEXEC)


def main():
    """
    :return: System return code
    """
    create_commit_hook()
    return 0


###########################################################################
if __name__ == '__main__':
    sys.exit(main())

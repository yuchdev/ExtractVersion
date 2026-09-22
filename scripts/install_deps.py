"""
Install/verify the external tools release-saga needs, on macOS, Linux, or Windows:

* awscli  - for --upload-s3
* gh      - for --create-release
* twine   - for --publish-pypi

Usage:
    python scripts/install_deps.py

This only installs the tools themselves; it does not configure credentials
(see the "Releasing" section of README.md for that).
"""

import platform
import shutil
import subprocess
import sys


def pip_install(*packages: str) -> None:
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", *packages], check=True)


def ensure_awscli() -> None:
    """awscli ships as a regular pip package, so this is identical on every OS."""
    if shutil.which("aws"):
        print("aws: already installed")
        return
    print("Installing awscli via pip...")
    pip_install("awscli")


def ensure_twine() -> None:
    if shutil.which("twine"):
        print("twine: already installed")
        return
    print("Installing twine via pip...")
    pip_install("twine")


def ensure_gh() -> None:
    """
    GitHub CLI has no pip package; fall back to each OS's native package manager
    when one is available, and print manual install instructions otherwise.
    """
    if shutil.which("gh"):
        print("gh: already installed")
        return

    system = platform.system()
    if system == "Darwin" and shutil.which("brew"):
        print("Installing GitHub CLI via Homebrew...")
        subprocess.run(["brew", "install", "gh"], check=True)
    elif system == "Windows" and shutil.which("winget"):
        print("Installing GitHub CLI via winget...")
        subprocess.run(["winget", "install", "--id", "GitHub.cli"], check=True)
    elif system == "Linux" and shutil.which("apt-get"):
        print("GitHub CLI not installed. On Debian/Ubuntu, install it with:")
        print("  sudo apt-get install gh")
        print("(see https://github.com/cli/cli/blob/trunk/docs/install_linux.md if 'gh' is unknown to apt)")
    else:
        print("Could not auto-install GitHub CLI on this platform.")
        print("Install it manually: https://github.com/cli/cli#installation")


def main() -> int:
    ensure_awscli()
    ensure_gh()
    ensure_twine()
    print()
    print("Next, configure credentials for whichever release steps you use:")
    print("  aws configure   (or an AWS_PROFILE / instance role) - for --upload-s3")
    print("  gh auth login                                       - for --create-release")
    print("  ~/.pypirc with a PyPI API token                     - for --publish-pypi")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import argparse
import json
import os
import pathlib
import sys
import tomllib
from abc import ABC, abstractmethod
from functools import lru_cache
from subprocess import CalledProcessError, run
from typing import Optional


@lru_cache(maxsize=1)
def get_package_info(config_path: str = "pyproject.toml") -> dict:
    """
    Read the package name and version from the [project] table of pyproject.toml.

    :param config_path: Path to the pyproject.toml file
    :return: Dict with keys: name, name_dash, version
    :raises RuntimeError: if the file, [project], or required fields are missing
    """
    if not os.path.isfile(config_path):
        raise RuntimeError(f"Cannot find {config_path}")
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    name = project.get("name")
    version = project.get("version")
    if not name or not version:
        raise RuntimeError(f"'name' and 'version' must be present in [project] of {config_path}")
    return {
        "name": name.replace("-", "_"),
        "name_dash": name.replace("_", "-"),
        "version": version,
    }


#
VERSION = get_package_info()["version"]

# Package-wide name with underscore (wheel filename)
PACKAGE_NAME = get_package_info()["name"]

# Name with dash (pip name, URL, S3 bucket)
PACKAGE_NAME_DASH = get_package_info()["name_dash"]

# Home dir
HOME = pathlib.Path.home()

PROJECT_DIR = os.path.abspath(str(os.path.join(os.path.dirname(os.path.realpath(__file__)))))

# Shared packages bucket; each package's objects live under a prefix named after PACKAGE_NAME_DASH
S3_BUCKET = "packages-s3-useast1-any"

PYTHON = sys.executable

PIP = [sys.executable, "-m", "pip"]


def executable_exists(executable):
    """
    :param executable: Name of the executable
    :return: True if executable exists, False otherwise
    """
    try:
        run([executable, "--version"])
        return True
    except FileNotFoundError:
        return False


def command_ok(cmd) -> bool:
    """
    Run a command purely as a live availability probe (e.g. "am I logged in",
    "are credentials valid"), swallowing its output.

    :param cmd: Command and arguments, as passed to subprocess.run
    :return: True iff the command exists and exits with status 0
    """
    try:
        return run(cmd, capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def sanity_check():
    """
    Check preconditions that aren't specific to any one release step (e.g. local package
    layout). Each release step's own `check()` validates its own tools/credentials live,
    right before it runs — see ReleaseStep and run_release_pipeline() below.
    """
    if not os.path.isdir(os.path.join(PROJECT_DIR, "src", PACKAGE_NAME)):
        print(f"Cannot find src/{PACKAGE_NAME}")
        sys.exit(1)


def wheel_path():
    """
    :return: Path to the wheel file
    """
    return os.path.join(PROJECT_DIR, "dist", f"{PACKAGE_NAME}-{VERSION}-py3-none-any.whl")


def uninstall_wheel():
    """
    pip.exe uninstall -y {PACKAGE_NAME_DASH}
    """
    run([*PIP, "uninstall", "-y", PACKAGE_NAME_DASH], check=True)


def build_wheel():
    """
    python.exe -m pip install --upgrade pip
    python.exe -m pip install --upgrade build
    python.exe -m build
    """
    run([PYTHON, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    run([PYTHON, "-m", "pip", "install", "--upgrade", "build"], check=True)
    run([PYTHON, "-m", "build"], check=True)


def install_wheel():
    """
    pip.exe install ./dist/{PACKAGE_NAME}-{VERSION}-py3-none-any.whl
    """
    run([*PIP, "install", wheel_path()], check=True)


def install_wheel_devmode():
    """
    pip.exe install -e ./dist/{PACKAGE_NAME}-{VERSION}-py3-none-any.whl
    """
    run([*PIP, "install", "-e", "."], check=True)


def cleanup_old_wheels():
    """
    Remove all previous {PACKAGE_NAME}-{VERSION}-py3-none-any.whl in dist
    """
    if os.path.isdir(os.path.join(PROJECT_DIR, "dist")):
        for file in os.listdir(os.path.join(PROJECT_DIR, "dist")):
            if file.startswith(f"{PACKAGE_NAME}-"):
                os.remove(os.path.join(PROJECT_DIR, "dist", file))


def release_version_exists(version):
    """
    Check if the version with respective release notes exists in RELEASE_NOTES.json
    :param version: Version to check in format 2.9.34
    :return: True if the version exists, False otherwise
    """
    with open(os.path.join(PROJECT_DIR, "RELEASE_NOTES.json")) as release_json:
        release_notes = json.load(release_json)
    return version in release_notes["releases"]


def tmp_release_notes():
    """
    Read the last release notes in JSON format from release_notes.json and create a temporary release notes file
    :return: Path to the temporary release notes file
    """
    # read release_notes.json as dict
    release_md = "RELEASE.md"
    with open("RELEASE_NOTES.json") as release_json:
        release_notes = json.load(release_json)

    if not release_version_exists(VERSION):
        print(f"No release notes found for version {VERSION}")
        sys.exit(1)

    last_release = release_notes["releases"][VERSION]["release_notes"]
    url_template = release_notes["release"]["download_link"]
    release_url = url_template.format(version=VERSION, package_name=PACKAGE_NAME, package_name_dash=PACKAGE_NAME_DASH)
    print(f"Last release notes: {last_release}")
    print(f"Download URL template: {url_template}")
    print(f"Download URL: {release_url}")

    # create a temporary release notes file
    with open(release_md, "w") as release_tmp:
        release_tmp.write("## Release notes\n")
        for note in last_release:
            release_tmp.write(f"* {note}\n")
        release_tmp.write("## Staging Area Download URL\n")
        release_tmp.write(f"[Wheel Package {VERSION} on AWS S3]({release_url})\n")
    return os.path.abspath(release_md)


def _log(message: str) -> None:
    print(f"[release] {message}", file=sys.stderr)


class ReleaseStep(ABC):
    """
    One stage of a release. Each concrete subclass owns both halves of one
    reversible action: `execute()` performs it, `rollback()` compensates for
    it, and `check()` is a live availability probe run immediately before
    `execute()` (not just once up front) — override it only when the step has
    a precondition to verify (a required CLI tool, valid credentials, being
    logged in, ...).

    `run_release_pipeline()` drives a list of steps as a Saga: if a step is
    unavailable or its `execute()` fails, every step that already completed
    is undone, in reverse order, via `rollback()` — and the failing step's
    own (possibly partial) effect is undone the same way. Steps should be
    ordered easiest-to-undo first and hardest-to-undo last, so that a late,
    hard-to-reverse step never leaves an earlier, cheaper one stranded.
    """

    name: str = "release step"

    def check(self) -> Optional[str]:
        """Return None if this step is available to run, else a reason it isn't."""
        return None

    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError


class UploadS3Step(ReleaseStep):
    name = "upload wheel to S3"

    def check(self) -> Optional[str]:
        if not executable_exists("aws"):
            return "awscli not installed"
        if not command_ok(["aws", "sts", "get-caller-identity"]):
            return "aws credentials are not configured or not valid (check `aws configure` / your profile)"
        return None

    def execute(self) -> None:
        """
        Example:
        aws s3 cp {PACKAGE_NAME}-{VERSION}-py3-none-any.whl s3://{S3_BUCKET}/{PACKAGE_NAME_DASH}/ --acl public-read
        """
        run(
            ["aws", "s3", "cp", wheel_path(), f"s3://{S3_BUCKET}/{PACKAGE_NAME_DASH}/", "--acl", "public-read"],
            check=True,
        )

    def rollback(self) -> None:
        """
        Example:
        aws s3 rm s3://{S3_BUCKET}/{PACKAGE_NAME_DASH}/{PACKAGE_NAME}-{VERSION}-py3-none-any.whl
        """
        key = f"{PACKAGE_NAME_DASH}/{os.path.basename(wheel_path())}"
        run(["aws", "s3", "rm", f"s3://{S3_BUCKET}/{key}"], check=True)


class GitTagStep(ReleaseStep):
    name = "tag release in git"

    def check(self) -> Optional[str]:
        if not executable_exists("git"):
            return "git not installed"
        if not command_ok(["git", "remote", "get-url", "origin"]):
            return "no 'origin' remote configured for this repository"
        return None

    def execute(self) -> None:
        """
        Example:
        git tag -a release.{VERSION} -m "Release {VERSION}"
        git push origin --tags master
        """
        run(["git", "tag", "-a", f"release.{VERSION}", "-m", f"Release {VERSION}"], check=True)
        run(["git", "push", "origin", "--tags", "master"], check=True)

    def rollback(self) -> None:
        """
        Example:
        git tag -d release.{VERSION}
        git push origin :refs/tags/release.{VERSION}
        """
        run(["git", "tag", "-d", f"release.{VERSION}"], check=True)
        run(["git", "push", "origin", f":refs/tags/release.{VERSION}"], check=True)


class GitHubReleaseStep(ReleaseStep):
    name = "create GitHub release"

    def check(self) -> Optional[str]:
        if not executable_exists("gh"):
            return "GitHub CLI (gh) not installed"
        if not command_ok(["gh", "auth", "status"]):
            return "gh is not logged in (run `gh auth login`)"
        if not release_version_exists(VERSION):
            return f"no release notes found for version {VERSION} in RELEASE_NOTES.json"
        return None

    def execute(self) -> None:
        """
        Example:
        gh release create release.{VERSION} dist/{PACKAGE_NAME}-{VERSION}-py3-none-any.whl \\
            --title {VERSION} --notes-file RELEASE.md
        """
        release_file = tmp_release_notes()
        try:
            run(
                [
                    "gh",
                    "release",
                    "create",
                    f"release.{VERSION}",
                    wheel_path(),
                    "--title",
                    VERSION,
                    "--notes-file",
                    release_file,
                ],
                check=True,
            )
        finally:
            os.remove(release_file)

    def rollback(self) -> None:
        """
        Example:
        gh release delete release.{VERSION} --yes
        """
        run(["gh", "release", "delete", f"release.{VERSION}", "--yes"], check=True)


class PublishPyPiStep(ReleaseStep):
    name = "publish to PyPI"

    def check(self) -> Optional[str]:
        if not executable_exists("twine"):
            return "twine not installed"
        if not os.path.isfile(os.path.join(HOME, ".pypirc")):
            return "no ~/.pypirc file found"
        return None

    def execute(self) -> None:
        """
        Example:
        twine upload dist/{PACKAGE_NAME}-{VERSION}-py3-none-any.whl
        """
        run([*PIP, "install", "--upgrade", "build", "twine"], check=True)
        run(["twine", "check", "dist/*"], check=True)
        run(["twine", "upload", "dist/*"], check=True)

    def rollback(self) -> None:
        # PyPI has no delete/overwrite API for an already-uploaded release file; the only
        # remedy is a manual "yank" from the web UI, so this can only warn, not undo.
        _log(
            f"WARNING: cannot auto-rollback a PyPI publish. If {PACKAGE_NAME}=={VERSION} was "
            f"actually uploaded, yank it manually at "
            f"https://pypi.org/manage/project/{PACKAGE_NAME_DASH}/release/{VERSION}/"
        )


def _rollback(steps: list[ReleaseStep]) -> None:
    """
    Best-effort compensation: run rollback() for each step in `steps`, in the
    order given by the caller (already reverse-chronological), never letting
    one failed rollback stop the rest.
    """
    for step in steps:
        _log(f"Rolling back: {step.name}")
        try:
            step.rollback()
        except Exception as exc:
            _log(f"WARNING: rollback of '{step.name}' also failed ({exc}). Manual cleanup is required for this step.")


def run_release_pipeline(steps: list[ReleaseStep]) -> None:
    """
    Execute release `steps` in order as a Saga with compensating transactions:
    stop and roll back everything already completed (plus the failing step's
    own partial effect) the moment a step is unavailable or raises.
    """
    completed: list[ReleaseStep] = []
    for step in steps:
        _log(f"Checking availability: {step.name}")
        reason = step.check()
        if reason is not None:
            _log(f"ERROR: '{step.name}' is not available: {reason}")
            _rollback(list(reversed(completed)))
            sys.exit(1)

        _log(f"Running: {step.name}")
        try:
            step.execute()
        except CalledProcessError as exc:
            _log(f"ERROR: '{step.name}' failed (command exited {exc.returncode}): {exc}")
            _rollback([step, *reversed(completed)])
            sys.exit(1)
        except Exception as exc:
            _log(f"ERROR: '{step.name}' failed: {exc}")
            _rollback([step, *reversed(completed)])
            sys.exit(1)
        else:
            _log(f"Completed: {step.name}")
            completed.append(step)

    _log(f"All {len(steps)} step(s) completed successfully")


def main() -> int:
    parser = argparse.ArgumentParser(description="Command-line params")
    parser.add_argument(
        "--mode",
        help="What to do with the package",
        choices=["build", "install", "dev", "reinstall", "uninstall"],
        default="reinstall",
        required=False,
    )
    parser.add_argument("--upload-s3", help="Upload the package to S3", action="store_true", required=False)
    parser.add_argument("--create-release", help="Create a release on GitHub", action="store_true", required=False)
    parser.add_argument(
        "--publish-pypi", help="Publish the package to PyPI server", action="store_true", default=False, required=False
    )
    args = parser.parse_args()

    print(f"Package name: {PACKAGE_NAME}")
    print(f"Package name2: {PACKAGE_NAME_DASH}")
    print(f"Version: {VERSION}")
    sanity_check()

    if args.mode == "build":
        build_wheel()
    elif args.mode == "install":
        cleanup_old_wheels()
        build_wheel()
        install_wheel()
    elif args.mode == "dev":
        cleanup_old_wheels()
        build_wheel()
        install_wheel_devmode()
    elif args.mode == "reinstall":
        cleanup_old_wheels()
        uninstall_wheel()
        build_wheel()
        install_wheel()
    elif args.mode == "uninstall":
        uninstall_wheel()
    else:
        print("Unknown mode")

    if args.mode != "uninstall":
        # Ordered easiest-to-undo first, hardest-to-undo (PyPI) last, so a failure late in
        # the pipeline never leaves a cheaper, already-reversible step stranded.
        steps: list[ReleaseStep] = []
        if args.upload_s3:
            steps.append(UploadS3Step())
        if args.create_release:
            steps.append(GitTagStep())
            steps.append(GitHubReleaseStep())
        if args.publish_pypi:
            steps.append(PublishPyPiStep())
        if steps:
            run_release_pipeline(steps)

    return 0


if __name__ == "__main__":
    sys.exit(main())

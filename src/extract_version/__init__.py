from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

# Version is stored in a single place: [project].version in pyproject.toml
try:
    __version__ = version("extract_version")
except PackageNotFoundError:
    __version__ = "0.0.0"

# Package root is 'src' directory
PACKAGE_ROOT = Path(__file__).parent

# Project root contains 'src' and 'test'
PROJECT_DIR = PACKAGE_ROOT.parent

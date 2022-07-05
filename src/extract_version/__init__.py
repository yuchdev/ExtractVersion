from pathlib import Path
from .version import VERSION

# Version is stored in a single place
__version__ = VERSION

# Package root is 'src' directory
PACKAGE_ROOT = Path(__file__).parent

# Project root contains 'src' and 'test'
PROJECT_DIR = PACKAGE_ROOT.parent

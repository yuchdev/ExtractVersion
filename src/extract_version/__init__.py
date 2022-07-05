from pathlib import Path
from .version import VERSION

__version__ = VERSION
logger = logging.getLogger(__name__)

# Package root is 'src' directory
PACKAGE_ROOT = Path(__file__).parent

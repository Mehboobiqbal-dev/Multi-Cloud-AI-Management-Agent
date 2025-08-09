import os
import sys

# Ensure the backend directory is on sys.path so absolute-style intra-package imports
# like `import core` or `from core.config import settings` resolve correctly.
_backend_dir = os.path.dirname(__file__)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from .memory import memory_instance
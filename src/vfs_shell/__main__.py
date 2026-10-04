"""Entry point: ``python -m vfs_shell``."""
import sys

from .app import main

if __name__ == "__main__":
    sys.exit(main())

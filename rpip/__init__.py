"""rpip - Resumable Package Installer.

A CLI tool that wraps pip to provide resumable downloads for Python packages.
Especially useful for large packages on unreliable internet connections.
"""

__version__ = "0.1.0"
__author__ = "SyBlock"
__email__ = "syblock.dev@gmail.com"

from rpip.main import main

__all__ = ["main", "__version__"]
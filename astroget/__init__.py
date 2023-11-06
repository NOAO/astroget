"""Find and get FITS metadata and images."""

import importlib.metadata

# List of packages to import when "from sparcl import *" is used
__all__ = ["client"]

# must mach: [N!]N(.N)*[{a|b|rc}N][.postN][.devN]
__version__ = "0.0.4a3.dev2"

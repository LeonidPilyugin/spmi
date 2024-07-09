"""Provides functions to load modules.
"""

import sys
import importlib.util
from pathlib import Path

def load_module(name: str, path: Path):
    """Loads module.

    Args:
        name (:obj:`str`): Module name.
        path (:obj:`pathlib.Path`): Path to module file.

    Returns:
        Loaded module.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    return module

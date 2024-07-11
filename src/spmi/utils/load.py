"""Provides functions to load modules.
"""

import sys
import importlib.util
from pathlib import Path

def load_module(name, path):
    """Loads module.

    Args:
        name (:obj:`str`): Module name.
        path (:obj:`pathlib.Path`): Path to module file.

    Returns:
        Loaded module.

    Raises:
        :class:`TypeError`
        :class:`ValueError`
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a string, not {type(name)}")
    if not isinstance(path, Path):
        raise TypeError(f"path must be a pathlib.Path, not {type(path)}")
    if not path.exists():
        raise ValueError(f"Path {path} doesn't exist")

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    return module

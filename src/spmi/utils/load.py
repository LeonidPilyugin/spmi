"""
.. module:: load.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

import sys
import importlib.util
from pathlib import Path

def load_module(name: str, path: Path):
    """Loads module

    Args:
        name (str): module name.
        path (:obj:`Path`): path to module file.

    Returns:
        module.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    return module



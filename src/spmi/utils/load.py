"""Provides functions to load modules.
"""

import sys
import inspect
import pkgutil
import importlib
from pathlib import Path

def load_class_from_package(classname, package):
    """Loads class from package by name.

    Iterates throw ``package`` modules and returns a class
    by ``classname`` if finds it.

    Args:
        classname (:obj:`str`): Classname.
        package (Python package): Package.

    Returns:
        :obj:`class`.

    Raises:
        :class:`TypeError`
        :class:`NotImplementedError`
    """
    if not isinstance(classname, str):
        raise TypeError(f"classname must be a str, not {type(classname)}")
    if not inspect.ismodule(package):
        raise TypeError(f"package must be a module, not {type(package)}")

    for (_, mname, _) in pkgutil.iter_modules([Path(package.__file__).parent]):
        module = importlib.import_module(package.__name__ + "." + mname)
        classes = inspect.getmembers(module, inspect.isclass)
        classes = list(filter(lambda x: x[0] == classname, classes))
        if len(classes) == 1:
            return classes[0][1]

    raise NotImplementedError(f"Cannot find \"{classname}\" in {package}")

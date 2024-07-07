"""
.. module:: hash.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

import hashlib
import os

def generate_hash(string: str = None, size=16) -> str:
    """Returns a hex hash string.

    Args:
        string (:obj:`Union[str, None]`): string to hash.
        If None, will generate a random hex string.
        size (int): size of hash.
    """
    return os.urandom(size).hex() if not string else hashlib.shake_256(string).hexdigest(size)

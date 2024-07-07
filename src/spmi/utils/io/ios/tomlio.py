"""
.. module:: tomlio.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

import toml
from spmi.utils.io.io import Io

class TomlIo(Io):
    """TOML formatted io"""

    def load(self):
        with open(self.path, encoding=self.encoding) as f:
            result = toml.load(f)
        return result

    def dump(self, data):
        with open(self.path, "w", encoding=self.encoding) as f:
            toml.dump(data, f)

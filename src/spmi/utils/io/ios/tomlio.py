"""Provides class :class:`TomlIo`.
"""

import toml
from spmi.utils.io.io import Io

class TomlIo(Io):
    """TOML formatted io."""

    def copy(self):
        return JsonIo(path=self.path, encoding=self.encoding)

    def load(self):
        with open(self.path, encoding=self.encoding) as f:
            result = toml.load(f)
        return result

    def dump(self, data):
        with open(self.path, "w", encoding=self.encoding) as f:
            toml.dump(data, f)

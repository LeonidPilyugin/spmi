"""Provides class :class:`TomlIo`.
"""

import toml
from spmi.utils.io.io import Io, IoException

class TomlIoException(IoException):
    pass

class TomlIo(Io):
    """TOML formatted io."""

    def copy(self):
        return JsonIo(path=self.path, encoding=self.encoding)

    def load(self):
        try:
            with open(self.path, encoding=self.encoding) as f:
                result = toml.load(f)
            return result
        except Exception as e:
            raise TomlIoException(f"Cannot load from \"{self.path}\":\n{e}") from e

    def dump(self, data):
        try:
            with open(self.path, "w", encoding=self.encoding) as f:
                toml.dump(data, f)
        except Exception as e:
            raise TomlIoException(f"Cannot dump to \"{self.path}\":\n{e}") from e

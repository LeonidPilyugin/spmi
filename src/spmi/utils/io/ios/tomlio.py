"""Provides class :class:`TomlIo`.
"""

import toml
from spmi.utils.io.io import Io, IoException

class TomlIoException(IoException):
    pass

class TomlIo(Io):
    """TOML formatted io."""

    def copy(self):
        return TomlIo(path=self.path)

    def load(self):
        super().load()
        try:
            result = toml.load(self._fd)
            return result
        except Exception as e:
            raise TomlIoException(f"Cannot load from \"{self.path}\":\n{e}") from e

    def dump(self, data):
        super().dump(data)
        try:
            toml.dump(data, self._fd)
        except Exception as e:
            raise TomlIoException(f"Cannot dump to \"{self.path}\":\n{e}") from e

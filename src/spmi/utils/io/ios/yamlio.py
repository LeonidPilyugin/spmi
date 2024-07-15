"""Provides class :class:`YamlIo`.
"""

import yaml
from spmi.utils.io.io import Io, IoException

class YamlIoException(IoException):
    pass

class YamlIo(Io):
    """Yaml formatted io."""

    def copy(self):
        return YamlIo(path=self.path, encoding=self.encoding)

    def load(self):
        super().load()
        try:
            result = yaml.safe_load(self._fd)
            return result
        except Exception as e:
            raise YamlIoException(f"Cannot load from \"{self.path}\":\n{e}") from e

    def dump(self, data):
        super().dump(data)
        try:
            yaml.dump(data, self._fd)
        except Exception as e:
            raise YamlIoException(f"Cannot dump to \"{self.path}\":\n{e}") from e

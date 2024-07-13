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
        try:
            with open(self.path, encoding=self.encoding) as f:
                result = yaml.safe_load(f)
            return result
        except Exception as e:
            raise YamlIoException(f"Cannot load from \"{self.path}\":\n{e}") from e

    def dump(self, data):
        try:
            with open(self.path, "w", encoding=self.encoding) as f:
                yaml.dump(data, f)
        except Exception as e:
            raise YamlIoException(f"Cannot dump to \"{self.path}\":\n{e}") from e

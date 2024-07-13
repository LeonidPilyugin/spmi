"""Provides class :class:`JsonIo`.
"""

import json
from spmi.utils.io.io import Io, IoException

class JsonIoException(IoException):
    pass

class JsonIo(Io):
    """JSON formatted io."""

    def copy(self):
        return JsonIo(path=self.path, encoding=self.encoding)

    def load(self):
        try:
            with open(self.path, encoding=self.encoding) as f:
                result = json.load(f)
            return result
        except Exception as e:
            raise JsonIoException(f"Cannot load from \"{self.path}\":\n{e}") from e

    def dump(self, data):
        try:
            with open(self.path, "w", encoding=self.encoding) as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            raise JsonIoException(f"Cannot dump to \"{self.path}\":\n{e}") from e

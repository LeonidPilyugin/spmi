"""Provides class :class:`JsonIo`.
"""

import json
from spmi.utils.io.io import Io, IoException

class JsonIoException(IoException):
    pass

class JsonIo(Io):
    """JSON formatted io."""

    def copy(self):
        return JsonIo(path=self.path)

    def load(self):
        super().load()
        try:
            result = json.load(self._fd)
            return result
        except Exception as e:
            raise JsonIoException(f"Cannot load from \"{self.path}\":\n{e}") from e

    def dump(self, data):
        super().dump(data)
        try:
            json.dump(data, self._fd, indent=4)
        except Exception as e:
            raise JsonIoException(f"Cannot dump to \"{self.path}\":\n{e}") from e

"""Provides class :class:`YamlIo`.
"""

import yaml
from spmi.utils.io.io import Io

class YamlIo(Io):
    """Yaml formatted io."""

    def copy(self):
        return YamlIo(path=self.path, encoding=self.encoding)

    def load(self):
        with open(self.path, encoding=self.encoding) as f:
            result = yaml.load(f)
        return result

    def dump(self, data):
        with open(self.path, "w", encoding=self.encoding) as f:
            yaml.dump(data, f)

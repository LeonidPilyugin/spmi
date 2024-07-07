"""
.. module:: jsonio.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

import json
from spmi.utils.io.io import Io

class JsonIo(Io):
    """JSON formatted io"""

    def load(self):
        with open(self.path, encoding=self.encoding) as f:
            result = json.load(f)
        return result

    def dump(self, data):
        with open(self.path, "w", encoding=self.encoding) as f:
            json.dump(data, f)

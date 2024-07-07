import sys
import json
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass


class Wrapper(metaclass=ABCMeta):
    def get_wrapper(self, arg=None):
        return 10
    pass

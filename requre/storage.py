# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from requre.cassette import Cassette
from .singleton import SingletonMeta


class PersistentObjectStorage(metaclass=SingletonMeta):
    def __init__(self):
        super().__init__()
        self.cassette = Cassette()

    def __getattr__(self, item):
        return getattr(self.cassette, item)

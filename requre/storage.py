# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import os

from requre.cassette import Cassette
from .singleton import SingletonMeta

logger = logging.getLogger(__name__)


class PersistentObjectStorage(metaclass=SingletonMeta):
    def __init__(self):
        super().__init__()
        self.cassette = Cassette()

    def __getattr__(self, item):
        return getattr(self.cassette, item)


class StorageCounter:
    counter = 0
    dir_suffix = "file_storage"
    previous = None

    @classmethod
    def reset_counter_if_changed(cls):
        current = os.path.basename(PersistentObjectStorage().storage_file)
        if cls.previous != current:
            cls.counter = 0
            cls.previous = current

    @classmethod
    def next(cls):
        cls.counter += 1
        return cls.counter

    @staticmethod
    def storage_file():
        return os.path.basename(PersistentObjectStorage().storage_file)

    @staticmethod
    def storage_dir():
        return os.path.dirname(PersistentObjectStorage().storage_file)

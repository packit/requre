# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


class SingletonMeta(type):
    """
    Metaclass for singleton, eg. to have right one object for persistent storage
    """

    _instance = None

    def __call__(self):
        if self._instance is None:
            self._instance = super().__call__()
        return self._instance

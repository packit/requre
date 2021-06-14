# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

"""
Exceptions for requre project
"""


class PersistentStorageException(Exception):
    """Exceptions for persistent storage of objects"""


class ItemNotInStorage(PersistentStorageException):
    pass


class StorageNoResponseLeft(PersistentStorageException):
    pass

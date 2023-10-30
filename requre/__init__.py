# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import contextlib
from importlib.metadata import PackageNotFoundError, distribution

from requre.base_testclass import RequreTestCase
from requre.record_and_replace import record, replace
from requre.cassette import Cassette
from requre.simple_object import Simple, Tuple
from requre.guess_object import Guess
from requre.helpers.files import StoreFiles
from requre.import_system import UpgradeImportSystem

with contextlib.suppress(PackageNotFoundError):
    __version__ = distribution(__name__).version

__all__ = [
    record.__name__,
    replace.__name__,
    RequreTestCase.__name__,
    Cassette.__name__,
    Simple.__name__,
    Tuple.__name__,
    Guess.__name__,
    StoreFiles.__name__,
    UpgradeImportSystem.__name__,
]

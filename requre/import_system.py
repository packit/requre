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


import builtins
import functools
from enum import Enum
from requre.constants import DEFAULT_IMPORT_FUNCTION
from typing import Optional, Any, Callable, List

from requre.storage import PersistentObjectStorage
from requre.cassette import Cassette
from requre.online_replacing import (
    ModuleRecord,
    _parse_and_replace_sys_modules,
    _revert_modules,
)


class ReplaceType(Enum):
    """
    Types for import system what are used in replacement list, to know ho to replace it:
    DECORATOR: decorate original function
    REPLACE: replace object by another one
    """

    DECORATOR = 1
    REPLACE = 2


def decorate(
    what: str,
    decorator: Callable,
) -> "UpgradeImportSystem":
    """
    Decorate the function when importing.

    :param what: what will be decorated
    :param decorator: decorator that will be used
    :return: UpgradeImportSystem
    """
    upgraded_import_system = UpgradeImportSystem()
    upgraded_import_system.decorate(what=what, decorator=decorator)
    return upgraded_import_system


def replace(
    what: str,
    replacement: Any,
) -> "UpgradeImportSystem":
    """
    Replace the module when importing.

    :param what: what will be replaced
    :param replacement: what will be used instead
    :return: UpgradeImportSystem
    """
    upgraded_import_system = UpgradeImportSystem()
    upgraded_import_system.replace(what=what, replacement=replacement)
    return upgraded_import_system


class UpgradeImportSystem:
    def __init__(self, cassette: Optional[Cassette] = None) -> None:
        self.cassette = cassette or PersistentObjectStorage().cassette
        self.module_list: List[ModuleRecord] = []

    def __enter__(self) -> "UpgradeImportSystem":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        builtins.__import__ = DEFAULT_IMPORT_FUNCTION
        self.revert()

    def revert(self) -> "UpgradeImportSystem":
        """
        Revert the changes to the import system.

        :return: self (chaining is supported)
        """
        builtins.__import__ = DEFAULT_IMPORT_FUNCTION
        _revert_modules(self.module_list)
        # TODO: fix reverting of 'from' modules
        self.module_list.clear()
        return self

    def decorate(self, what: str, decorator: Callable) -> "UpgradeImportSystem":
        """
        Decorate the function when importing.

        :param what: what will be decorated
        :param decorator: decorator that will be used
        :return: self (chaining is supported)
        """
        return self.upgrade(what, ReplaceType.DECORATOR, decorator)

    def replace(self, what: str, replacement: Any) -> "UpgradeImportSystem":
        """
        Replace the module when importing.

        :param what: what will be replaced
        :param replacement: what will be used instead
        :return: self (chaining is supported)
        """

        return self.upgrade(what, ReplaceType.REPLACE, replacement)

    def upgrade(self, what, replace_type, replacement, add_revert_list=[]):
        """
        Apply the upgrade of modules (already loaded or when import of the module comes)

        :param what: what to update
        :param replace_type: type of replacement ReplaceType
        :param replacement: replaced or decorator to be applied
        :param add_revert_list: append anoher part where revert has to happen.
                                In case of some from statements it may lead that
                                they are not properly reverted as well.
        :return: self (chaining is supported)
        """
        self._upgrade_filter(what, replace_type, replacement, add_revert_list)
        return self

    def _upgrade_filter(
        self,
        what,
        replace_type,
        replacement,
        add_revert_list,
        func=DEFAULT_IMPORT_FUNCTION,
    ):
        replace = None
        decorate = None
        if replace_type == ReplaceType.REPLACE:
            replace = replacement
        elif replace_type == ReplaceType.DECORATOR:
            decorate = replacement
        # check if already loaded inside sys.modules, then do not apply update of import system
        recorded_items = _parse_and_replace_sys_modules(
            what=what,
            cassette=self.cassette,
            decorate=decorate,
            replace=replace,
            add_revert_list=add_revert_list,
        )
        if recorded_items:
            self.module_list += recorded_items
            return

        @functools.wraps(func)
        def new_import(*args, **kwargs):
            with open("debug.file", "w") as fd:
                fd.write("eee", what, args, kwargs)
            out = func(*args, **kwargs)
            recorded_items = _parse_and_replace_sys_modules(
                what=what,
                cassette=self.cassette,
                decorate=decorate,
                replace=replace,
                add_revert_list=add_revert_list,
            )
            if recorded_items:
                self.module_list += recorded_items
            return out

        func = new_import

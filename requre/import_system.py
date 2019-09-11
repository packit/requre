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


import inspect
import functools
import re
import builtins
from enum import Enum
from typing import Callable, Optional, Any

ORIGIN_IMPORT = builtins.__import__

class ReplaceType(Enum):
    """
    Types for import system what are used in replacement list, to know ho to replace it:
    DECORATOR: decorate original function
    REPLACE: replace object by another one
    REPLACE_MODULE: replace whole module by another implementation
    """
    DECORATOR = 1
    REPLACE = 2
    REPLACE_MODULE = 3


def _upgrade_import_system(
    func: Callable, name_filters: list, debug_file: Optional[str] = None
) -> Any:
    """
    Internal function what replace import function by decorated one, what is able to do replaces
    inside them
    :param func: buildin.__import__ is original purpose
    :param name_filters: list of filters with replacements
    :param debug_file: file where to store debug information about replacements
    :return: called import function
    """
    @functools.wraps(func)
    def new_import(*args, **kwargs):
        out = func(*args, **kwargs)
        name = list(args)[0]

        for filter_item in name_filters:
            one_filter = filter_item[0]
            additional_filters = filter_item[1]
            if re.search(one_filter, name):
                mod = inspect.getmodule(inspect.stack()[1][0])
                fromlist = ()
                if len(args) > 3:
                    fromlist = list(args)[3]
                module_name = getattr(mod, "__name__", "")
                module_file = getattr(mod, "__file__", "")
                item = {
                    "module_object": out,
                    "who": mod,
                    "who_name": module_name,
                    "who_filename": module_file,
                    "fromlist": fromlist,
                }

                if all([re.search(v, item[k]) for k, v in additional_filters.items()]):
                    text = list()
                    text.append(
                        f"{module_name} ({module_file})-> {name} ({fromlist})\n"
                    )
                    if len(filter_item) > 2:
                        for key, replacement in filter_item[2].items():
                            replace_type = replacement[0]
                            replace_object = replacement[1]
                            original_obj = out
                            parent_obj = out
                            # traverse into
                            if len(key) > 0:
                                for key_item in key.split("."):
                                    parent_obj = original_obj
                                    original_obj = getattr(original_obj, key_item)
                            if replace_type == ReplaceType.REPLACE:
                                setattr(
                                    parent_obj, original_obj.__name__, replace_object
                                )
                                text.append(
                                    f"\treplacing {key} by function {replace_object.__name__}\n"
                                )
                            elif replace_type == ReplaceType.DECORATOR:
                                setattr(
                                    parent_obj,
                                    original_obj.__name__,
                                    replace_object(original_obj),
                                )
                                text.append(
                                    f"\tdecorate {key}  by {replace_object.__name__}\n"
                                )
                            elif replace_type == ReplaceType.REPLACE_MODULE:
                                out = replace_object
                                text.append(
                                    f"\treplace module {module_name} by {replace_object.__name__}\n"
                                )
                    if debug_file:
                        with open(debug_file, "a") as fd:
                            fd.write("".join(text))
        return out

    return new_import


def upgrade_import_system(filters, debug_file: Optional[str] = None):
    """
    High level upgrade import function, do not allow to pass what to replace,
    because it is builtins.__import__
    :param filters: list of filters, for examples see: tests/test_import_system.py
    :param debug_file: file where to store debug information about replacements
    :return: decorated import system
    """
    builtins.__import__ = _upgrade_import_system(
        builtins.__import__, name_filters=filters, debug_file=debug_file
    )


def revert_import_system():
    """
    Revert import system back to original nondecorated function
    :return: None
    """
    builtins.__import__ = ORIGIN_IMPORT

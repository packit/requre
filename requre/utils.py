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
import logging
import shlex
import subprocess
from enum import Enum
from pathlib import Path
from typing import Union, Any, Optional, Dict, List

from requre.exceptions import PersistentStorageException
from requre.constants import METATADA_KEY

logger = logging.getLogger(__name__)


class StorageMode(Enum):
    default = 0
    read = 1
    write = 2
    append = 3


def run_command(cmd, error_message=None, cwd=None, fail=True, output=False):
    """
    subprocess wrapper, copied from packit, for higher level handling of executiong commands,
    :param cmd:
    :param error_message:
    :param cwd:
    :param fail:
    :param output:
    :return:
    """
    if not isinstance(cmd, list):
        cmd = shlex.split(cmd)

    logger.debug("cmd = '%s'", " ".join(cmd))

    cwd = cwd or str(Path.cwd())
    error_message = error_message or f"Command {cmd} failed."

    shell = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        cwd=cwd,
        universal_newlines=True,
    )

    if not output:
        # output is returned, let the caller process it
        logger.debug("%s", shell.stdout)
    stderr = shell.stderr.strip()
    if stderr:
        logger.error("%s", shell.stderr)

    if shell.returncode != 0:
        logger.error("Command %s failed", shell.args)
        logger.error("%s", error_message)
        if fail:
            raise PersistentStorageException(
                f"Command {shell.args!r} failed: {error_message}"
            )
        success = False
    else:
        success = True

    if not output:
        return success
    return shell.stdout


class Replacement:
    def __init__(self, name, key, parent, one_filter, replacement) -> None:
        self.name = name
        self.key = key
        self.parent = parent
        self.filter = one_filter
        self.replacement = replacement


class DictProcessing:
    def __init__(self, requre_dict: dict):
        self.requre_dict = requre_dict

    def match(self, selector: list, internal_object: Union[dict, list, None] = None):
        if internal_object is None:
            internal_object = self.requre_dict
        if len(selector) == 0:
            logger.debug(f"all selectors matched")
            yield internal_object
            # add return here, to avoid multiple returns
            return
        if isinstance(internal_object, dict):
            for k, v in internal_object.items():
                if v is None:
                    return
                if selector and selector[0] == k:
                    logger.debug(f"selector {k} matched")
                    yield from self.match(selector=selector[1:], internal_object=v)
                else:
                    yield from self.match(selector=selector, internal_object=v)
        elif isinstance(internal_object, list):
            for list_item in internal_object:
                if list_item is None:
                    return
                yield from self.match(selector=selector, internal_object=list_item)
        else:
            return

    @staticmethod
    def replace(obj: Any, key: Any, value: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    logger.debug(f"replacing: {obj[key]} by {value}")
                    obj[key] = value
                else:
                    DictProcessing.replace(obj=v, key=key, value=value)
        if isinstance(obj, list):
            for item in obj:
                DictProcessing.replace(obj=item, key=key, value=value)

    def simplify(
        self, internal_object: Optional[Dict] = None, ignore_list: Optional[List] = None
    ):
        if ignore_list is None:
            ignore_list = []
        if internal_object is None:
            internal_object = self.requre_dict
        if isinstance(internal_object, dict):
            if len(internal_object.keys()) == 1:
                key = list(internal_object.keys())[0]
                if key in [METATADA_KEY] + ignore_list:
                    return
                if isinstance(internal_object[key], dict):
                    value = internal_object.pop(key)
                    print(
                        f"Removing key: {key}  and continue with {list(value.keys())}"
                    )
                    for k, v in value.items():
                        internal_object[k] = v
                        self.simplify(
                            internal_object=internal_object, ignore_list=ignore_list
                        )
            else:
                for v in internal_object.values():
                    self.simplify(internal_object=v, ignore_list=ignore_list)


def get_module_of_previous_context():
    current_ctx = inspect.currentframe()
    while True:
        current_ctx = current_ctx.f_back
        frameinfo_args = (current_ctx,) + inspect.getframeinfo(current_ctx, 1)
        frameinfo = inspect.FrameInfo(*frameinfo_args)
        module = inspect.getmodule(frameinfo[0])
        if module and not module.__name__.startswith("requre"):
            return module

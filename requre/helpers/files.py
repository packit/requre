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


import os
import logging
import shutil
import functools
from typing import Callable, Any, Dict

from requre.storage import PersistentObjectStorage
from requre.utils import run_command, get_if_recording, STORAGE
from requre.helpers.function_output import store_function_output

logger = logging.getLogger(__name__)


def _copy_logic(
    pers_storage: PersistentObjectStorage, source: str, destination: str
) -> None:
    """
    Internal function. Copy files to or back from persistent STORAGE location
    """
    logger.debug(f"Copy files {source} -> {destination}")
    logger.debug(f"Persistent Storage write mode: {pers_storage.is_write_mode}")
    if pers_storage.is_write_mode:
        if os.path.isdir(source):
            os.makedirs(destination)
            run_command(cmd=["cp", "-drT", source, destination])
        else:
            run_command(cmd=["cp", "-d", source, destination])
    else:
        if os.path.isdir(destination):
            if os.path.exists(source):
                shutil.rmtree(source)
            os.makedirs(source)
            run_command(cmd=["cp", "-drTf", destination, source])
        else:
            run_command(cmd=["cp", "-df", destination, source])


def store_files_return_value(func: Callable) -> Any:
    @functools.wraps(func)
    def store_files_int(*args, **kwargs):
        if not get_if_recording():
            return func(*args, **kwargs)
        else:
            data_dir = os.path.dirname(STORAGE.storage_file)
            current_dir = os.path.join(data_dir, str(STORAGE.dir_count))
            os.makedirs(data_dir, exist_ok=True)
            STORAGE.dir_count += 1
            output = store_function_output(func)(*args, **kwargs)
            _copy_logic(STORAGE, output, current_dir)
        return output

    return store_files_int


def store_files_guess_args(func: Callable) -> Any:
    @functools.wraps(func)
    def store_files_int(*args, **kwargs):
        if not get_if_recording():
            return func(*args, **kwargs)
        else:
            data_dir = os.path.dirname(STORAGE.storage_file)
            current_dir = os.path.join(data_dir, str(STORAGE.dir_count))
            os.makedirs(current_dir, exist_ok=True)
            STORAGE.dir_count += 1
            output = store_function_output(func)(*args, **kwargs)
            if STORAGE.is_write_mode:
                for position in range(len(args)):
                    arg = args[position]
                    if not isinstance(arg, str):
                        continue
                    if os.path.exists(arg):
                        current_path = os.path.join(current_dir, str(position))
                        _copy_logic(STORAGE, arg, current_path)
                for k, v in kwargs.items():
                    if os.path.exists(v):
                        current_path = os.path.join(current_dir, k)
                        _copy_logic(STORAGE, v, current_path)
            else:
                for item in os.listdir(current_dir):
                    current_path = os.path.join(current_dir, item)
                    if item.isdigit():
                        arg = args[int(item)]
                    else:
                        arg = kwargs[item]
                    _copy_logic(STORAGE, arg, current_path)
        return output

    return store_files_int


def store_files_arg_references(files_params: Dict) -> Any:
    """
    files_params = {"target_dir": 2}
    """

    def store_files_int(func):
        @functools.wraps(func)
        def store_files_int_int(*args, **kwargs):
            if not get_if_recording():
                return func(*args, **kwargs)
            else:
                data_dir = os.path.dirname(STORAGE.storage_file)
                output = store_function_output(func)(*args, **kwargs)
                for key, position in files_params.items():
                    if key in kwargs:
                        param = kwargs[key]
                    else:
                        param = args[position]
                    current_path = os.path.join(data_dir, str(STORAGE.dir_count))
                    STORAGE.dir_count += 1
                    _copy_logic(STORAGE, param, current_path)
            return output

        return store_files_int_int

    return store_files_int

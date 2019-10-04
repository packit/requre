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


class StoreFiles:
    counter = 0
    dir_suffix = "file_storage"
    previous = None
    current = None

    @classmethod
    def _get_data_dir(cls):
        dirname = os.path.dirname(STORAGE.storage_file)
        additional = f"{os.path.basename(STORAGE.storage_file)}.{cls.dir_suffix}"
        output = os.path.join(dirname, additional)
        os.makedirs(output, exist_ok=True)
        # reset counter if output directory is switched, to ensure that you always start from zero
        if cls.current != output:
            cls.counter = 0
            cls.previous = cls.current
            cls.current = output
        return output

    @classmethod
    def _next(cls):
        cls.counter += 1
        return cls.counter

    @classmethod
    def _next_directory_name(cls):
        return os.path.join(cls._get_data_dir(), str(cls._next()))

    @staticmethod
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

    @classmethod
    def return_value(cls, func: Callable) -> Any:
        """
        Decorator what will store return value of function/method as file and will store content

        """
        @functools.wraps(func)
        def store_files_int(*args, **kwargs):
            if not get_if_recording():
                return func(*args, **kwargs)
            else:
                current_dir = cls._next_directory_name()
                os.makedirs(cls._get_data_dir(), exist_ok=True)
                output = store_function_output(func)(*args, **kwargs)
                cls._copy_logic(STORAGE, output, current_dir)
            return output

        return store_files_int

    @classmethod
    def guess_args(cls, func: Callable) -> Any:
        """
        Decorator what try to guess, which arg is file or directory and store its content
        """
        @functools.wraps(func)
        def store_files_int(*args, **kwargs):
            if not get_if_recording():
                return func(*args, **kwargs)
            else:
                current_dir = cls._next_directory_name()
                os.makedirs(current_dir, exist_ok=True)
                output = store_function_output(func)(*args, **kwargs)
                if STORAGE.is_write_mode:
                    for position in range(len(args)):
                        arg = args[position]
                        if not isinstance(arg, str):
                            continue
                        if os.path.exists(arg):
                            current_path = os.path.join(current_dir, str(position))
                            cls._copy_logic(STORAGE, arg, current_path)
                    for k, v in kwargs.items():
                        if os.path.exists(v):
                            current_path = os.path.join(current_dir, k)
                            cls._copy_logic(STORAGE, v, current_path)
                else:
                    for item in os.listdir(current_dir):
                        current_path = os.path.join(current_dir, item)
                        if item.isdigit():
                            arg = args[int(item)]
                        else:
                            arg = kwargs[item]
                        cls._copy_logic(STORAGE, arg, current_path)
            return output

        return store_files_int

    @classmethod
    def arg_references(cls, files_params: Dict) -> Any:
        """
        Decorator what will store files or directory based on arguments,
        you have to pass name and position of arg via dict
        (be careful about counting self or cls parameteres for methods)
        eg. files_params = {"target_dir": 2}
        """

        def store_files_int(func):
            @functools.wraps(func)
            def store_files_int_int(*args, **kwargs):
                if not get_if_recording():
                    return func(*args, **kwargs)
                else:
                    output = store_function_output(func)(*args, **kwargs)
                    for key, position in files_params.items():
                        if key in kwargs:
                            param = kwargs[key]
                        else:
                            param = args[position]
                        current_path = cls._next_directory_name()
                        cls._copy_logic(STORAGE, param, current_path)
                return output

            return store_files_int_int

        return store_files_int

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


import functools
import logging
import os
import tarfile
from io import BytesIO
from typing import Any, Dict, Optional, Union, Callable, Type

from requre.exceptions import PersistentStorageException
from requre.helpers.simple_object import Simple
from requre.helpers.guess_object import Guess
from requre.objects import ObjectStorage
from requre.cassette import Cassette, CassetteExecution, StorageMode

logger = logging.getLogger(__name__)


def return_cls_type(cassette) -> Union[Type[Simple], Type[Guess]]:
    if cassette.storage_file_version < 3:
        return Simple
    else:
        return Guess


class StoreFiles(ObjectStorage):
    dir_suffix = "file_storage"
    tar_compression = "xz"
    basic_ps_keys = ["X", "file", "tar"]
    _cassette: Cassette = None

    @staticmethod
    def _test_identifier(cassette):
        return os.path.basename(cassette.storage_file)

    @staticmethod
    def store_file_content(cassette: Cassette, content: Any, file_name: str):
        generated = f"{os.path.basename(cassette.storage_file)}.{file_name}_"
        target_dir = os.path.realpath(os.path.dirname(cassette.storage_file))
        # generate unique number for each file store to avoid rewrite current content
        # increase highest number
        suffix = f".tar.{StoreFiles.tar_compression}"
        existing_nums = sorted(
            [
                int(x.replace(generated, "").replace(suffix, ""))
                for x in os.listdir(target_dir)
                if x.startswith(generated)
            ]
        )
        next_num = 1 if not existing_nums else existing_nums[-1] + 1
        file_path = os.path.join(target_dir, f"{generated}{next_num}{suffix}")
        with open(file_path, "wb") as outfile:
            outfile.write(content)
        # return properly generated unique file name
        return os.path.basename(file_path)

    @staticmethod
    def read_file_content(
        cassette: Cassette, file_name: str, root_dir: Optional[str] = None
    ):
        file_path = os.path.realpath(
            os.path.join(os.path.dirname(cassette.storage_file), file_name)
        )
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"requre cannot read from file {file_path}, does not existsin dir: {root_dir})"
            )
        with open(file_path, "rb") as infile:
            content = infile.read()
        return content

    @classmethod
    def _copy_logic(cls, cassette: Cassette, pathname: str, keys: list) -> None:
        """
        Internal function. Copy files to or back from persisten storage
        It will create tar archive with tar_compression and stores it to Persistent Storage
        """
        logger.debug(f"Copy files {pathname} -> {keys}")
        logger.debug(f"Persistent Storage mode: {cassette.mode}")
        original_cwd = os.getcwd()
        if cassette.do_store(keys=cls.basic_ps_keys + keys):
            try:
                artifact_name = os.path.basename(pathname)
                artifact_path = os.path.dirname(pathname)
                os.chdir(artifact_path)
                with BytesIO() as fileobj:
                    with tarfile.open(
                        mode=f"x:{cls.tar_compression}", fileobj=fileobj
                    ) as tar_store:
                        tar_store.add(name=artifact_name)
                    metadata = {cassette.data_miner.LATENCY_KEY: 0}
                    file_name = cls.store_file_content(
                        cassette=cassette,
                        file_name=os.path.basename(pathname),
                        content=fileobj.getvalue(),
                    )
                    cassette.store(
                        keys=cls.basic_ps_keys + keys,
                        values=file_name,
                        metadata=metadata,
                    )
            finally:
                os.chdir(original_cwd)
        else:
            value = cassette[cls.basic_ps_keys + keys]
            content = cls.read_file_content(cassette=cassette, file_name=value)
            with BytesIO(content) as fileobj:
                with tarfile.open(
                    mode=f"r:{cls.tar_compression}", fileobj=fileobj
                ) as tar_store:
                    tarinfo_1st_member = tar_store.getmembers()[0]
                    if tarinfo_1st_member.isfile():
                        with open(pathname, mode="wb") as output_file:
                            output_file.write(
                                tar_store.extractfile(tarinfo_1st_member).read()
                            )
                    else:
                        for tar_item in tar_store.getmembers():
                            # we have to modify path of files to remove topdir
                            if len(tar_item.name.split(os.path.sep, 1)) > 1:
                                tar_item.name = tar_item.name.split(os.path.sep, 1)[1]
                            else:
                                tar_item.name = "."
                            try:
                                tar_store.extract(tar_item, path=pathname)
                            except IOError:
                                # rewrite readonly files if necessary
                                os.remove(os.path.join(pathname, tar_item.name))
                                tar_store.extract(tar_item, path=pathname)

    @classmethod
    def where_file_as_return_value(
        cls,
        cassette: Optional[Cassette] = None,
        return_decorator: Optional[Callable] = None,
    ) -> Any:
        """
        Decorator what will store return value of function/method as file and will store content

        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance

        """
        casex = CassetteExecution()
        casex.cassette = cassette or cls.get_cassette()
        casex.obj_cls = cls
        if not return_decorator:
            return_decorator = return_cls_type(casex.cassette).decorator_plain

        def internal(func):
            @functools.wraps(func)
            def store_files_int(*args, **kwargs):
                output = return_decorator(cassette=casex.cassette)(func)(
                    *args, **kwargs
                )
                cls._copy_logic(
                    cassette=casex.cassette,
                    pathname=output,
                    keys=[cls.__name__, cls._test_identifier(casex.cassette)],
                )
                return output

            return store_files_int

        casex.function = internal
        return casex

    @classmethod
    def guess_files_from_parameters(
        cls,
        cassette: Optional[Cassette] = None,
        return_decorator: Optional[Callable] = None,
    ) -> Any:
        """
        Decorator what try to guess, which arg is file or directory and store its content

        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """
        casex = CassetteExecution()
        casex.cassette = cassette or cls.get_cassette()
        casex.obj_cls = cls
        if not return_decorator:
            return_decorator = return_cls_type(casex.cassette).decorator_plain

        def internal(func):
            @functools.wraps(func)
            def store_files_int(*args, **kwargs):
                def int_dec_fn(pathname_arg, keys_arg):
                    if not isinstance(pathname_arg, str):
                        return
                    if casex.cassette.do_store(
                        keys=StoreFiles.basic_ps_keys + keys_arg
                    ):
                        if os.path.exists(pathname_arg):
                            cls._copy_logic(
                                cassette=casex.cassette,
                                pathname=pathname_arg,
                                keys=keys_arg,
                            )
                    else:
                        try:
                            cls._copy_logic(
                                cassette=casex.cassette,
                                pathname=pathname_arg,
                                keys=keys_arg,
                            )
                        except PersistentStorageException:
                            pass

                class_test_id_list = [
                    cls.__name__,
                    cls._test_identifier(casex.cassette),
                ]
                output = return_decorator(cassette=casex.cassette)(func)(
                    *args, **kwargs
                )
                for position in range(len(args)):
                    int_dec_fn(args[position], class_test_id_list + [position])
                for k, v in kwargs.items():
                    int_dec_fn(v, class_test_id_list + [k])
                return output

            return store_files_int

        casex.function = internal
        return casex

    @classmethod
    def where_arg_references(
        cls,
        key_position_params_dict: Dict,
        cassette: Optional[Cassette] = None,
        return_decorator: Optional[Callable] = None,
    ) -> Any:
        """
        Decorator what will store files or directory based on arguments,
        you have to pass name and position of arg via dict
        (be careful about counting self or cls parameteres for methods)
        eg. key_position_params_dict = {"target_dir": 2}

        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """
        casex = CassetteExecution()
        casex.cassette = cassette or cls.get_cassette()
        casex.obj_cls = cls
        if not return_decorator:
            return_decorator = return_cls_type(casex.cassette).decorator_plain

        def internal(func):
            @functools.wraps(func)
            def store_files_int_int(*args, **kwargs):
                class_test_id_list = [
                    cls.__name__,
                    cls._test_identifier(casex.cassette),
                ]
                if casex.cassette.mode != StorageMode.read:
                    output = return_decorator(cassette=casex.cassette)(func)(
                        *args, **kwargs
                    )
                for key, position in key_position_params_dict.items():
                    if key in kwargs:
                        param = kwargs[key]
                    else:
                        param = args[position]
                    cls._copy_logic(
                        cassette=casex.cassette,
                        pathname=param,
                        keys=class_test_id_list + [key],
                    )
                if casex.cassette.mode == StorageMode.read:
                    output = return_decorator(cassette=casex.cassette)(func)(
                        *args, **kwargs
                    )

                return output

            return store_files_int_int

        casex.function = internal
        return casex

    @classmethod
    def explicit_reference(
        cls,
        file_param: str,
        dest_key: str = "default",
        cassette: Optional[Cassette] = None,
        return_decorator: Optional[Callable] = None,
    ) -> Any:
        """
        Method to store explicitly path file_param to persistent storage

        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """
        casex = CassetteExecution()
        casex.cassette = cassette or cls.get_cassette()
        casex.obj_cls = cls
        if not return_decorator:
            return_decorator = return_cls_type(casex.cassette).decorator_plain

        def internal(func):
            @functools.wraps(func)
            def store_files_int(*args, **kwargs):
                class_test_id_list = [
                    cls.__name__,
                    cls._test_identifier(casex.cassette),
                ]
                if casex.cassette.mode != StorageMode.read:
                    output = return_decorator(cassette=casex.cassette)(func)(
                        *args, **kwargs
                    )
                cls._copy_logic(
                    cassette=casex.cassette,
                    pathname=file_param,
                    keys=class_test_id_list + [dest_key],
                )
                if casex.cassette.mode == StorageMode.read:
                    output = return_decorator(cassette=casex.cassette)(func)(
                        *args, **kwargs
                    )
                return output

            return store_files_int

        casex.function = internal
        return casex

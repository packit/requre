# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import functools
import logging
import os
import tarfile
from io import BytesIO
from typing import Any, Dict, Optional, Type, Union

from requre.cassette import Cassette, CassetteExecution, StorageMode
from requre.exceptions import PersistentStorageException
from requre.guess_object import Guess
from requre.objects import ObjectStorage
from requre.simple_object import Simple

logger = logging.getLogger(__name__)


def return_cls_type(cassette: Optional[Cassette]) -> Union[Type[Simple], Type[Guess]]:
    if cassette and cassette.storage_file_version < 3:
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
            int(x.replace(generated, "").replace(suffix, ""))
            for x in os.listdir(target_dir)
            if x.startswith(generated)
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
    def __write_file(cls, content, pathname):
        with BytesIO(content) as fileobj:
            with tarfile.open(
                mode=f"r:{cls.tar_compression}", fileobj=fileobj
            ) as tar_store:
                members = tar_store.getmembers()
                tarinfo_1st_member = members[0]
                if tarinfo_1st_member.isfile():
                    with open(pathname, mode="wb") as output_file:
                        output_file.write(
                            tar_store.extractfile(tarinfo_1st_member).read()
                        )
                    return
                for tar_item in members:
                    # we have to modify path of files to remove topdir
                    if len(tar_item.name.split(os.path.sep, 1)) > 1:
                        tar_item.name = tar_item.name.split(os.path.sep, 1)[1]
                    else:
                        tar_item.name = "."
                    try:
                        tar_store.extract(tar_item, path=pathname)
                    except OSError:
                        # rewrite readonly files if necessary
                        os.remove(os.path.join(pathname, tar_item.name))
                        tar_store.extract(tar_item, path=pathname)

    @classmethod
    def _copy_logic(
        cls,
        cassette: Cassette,
        pathname: str,
        keys: list,
        ret_store_cls: Any,
        return_value: Any,
    ) -> Any:
        """
        Internal function. Copy files to or back from persisten storage
        It will create tar archive with tar_compression and stores it to Persistent Storage
        """
        FILENAME = "filename"
        TARGET_PATH = "target_path"
        RETURNED = "return_value"
        serialization = ret_store_cls(store_keys=["not_important"], cassette=cassette)
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
                    serialized = serialization.to_serializable(return_value)
                    output = {
                        FILENAME: file_name,
                        RETURNED: serialized,
                        TARGET_PATH: pathname,
                    }
                    cassette.store(
                        keys=cls.basic_ps_keys + keys,
                        values=output,
                        metadata=metadata,
                    )
            finally:
                os.chdir(original_cwd)
        else:
            output = cassette[cls.basic_ps_keys + keys]
            pathname = pathname or output[RETURNED]
            content = cls.read_file_content(
                cassette=cassette, file_name=output[FILENAME]
            )
            # WORKAROUND: some parts expects old dir and some new one. so copy to both to ensure.
            # mainly when creating complex objects.
            for item in [pathname, output[TARGET_PATH]]:
                cls.__write_file(content, item)
            return_value = serialization.from_serializable(output[RETURNED])
        return return_value

    @classmethod
    def __get_executor_and_return_cls(cls, cassette, output_cls):
        casex = CassetteExecution()
        casex.cassette = cassette or cls.get_cassette()
        casex.obj_cls = cls
        if not output_cls:
            output_cls = return_cls_type(cassette)
        return casex, output_cls

    @classmethod
    def where_file_as_return_value(
        cls,
        cassette: Optional[Cassette] = None,
        output_cls: Optional[Any] = None,
    ) -> Any:
        """
        Decorator what will store return value of function/method as file and will store content

        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance

        """
        casex, output_cls = cls.__get_executor_and_return_cls(cassette, output_cls)

        def internal(func):
            @functools.wraps(func)
            def store_files_int(*args, **kwargs):
                output = None
                if casex.cassette.mode != StorageMode.read:
                    output = func(*args, **kwargs)
                output = cls._copy_logic(
                    cassette=casex.cassette,
                    pathname=output,
                    keys=[cls.__name__, cls._test_identifier(casex.cassette)],
                    ret_store_cls=output_cls,
                    return_value=output,
                )
                return output

            return store_files_int

        casex.function = internal
        return casex

    @classmethod
    def guess_files_from_parameters(
        cls,
        cassette: Optional[Cassette] = None,
        output_cls: Optional[Any] = None,
    ) -> Any:
        """
        Decorator what try to guess, which arg is file or directory and store its content

        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """
        casex, output_cls = cls.__get_executor_and_return_cls(cassette, output_cls)

        def internal(func):
            @functools.wraps(func)
            def store_files_int(*args, **kwargs):
                output = None
                if casex.cassette.mode != StorageMode.read:
                    output = func(*args, **kwargs)

                def int_dec_fn(pathname_arg, keys_arg):
                    if not isinstance(pathname_arg, str):
                        return
                    if casex.cassette.do_store(
                        keys=StoreFiles.basic_ps_keys + keys_arg
                    ):
                        if os.path.exists(pathname_arg):
                            return cls._copy_logic(
                                cassette=casex.cassette,
                                pathname=pathname_arg,
                                keys=keys_arg,
                                ret_store_cls=output_cls,
                                return_value=output,
                            )
                    else:
                        try:
                            return cls._copy_logic(
                                cassette=casex.cassette,
                                pathname=pathname_arg,
                                keys=keys_arg,
                                ret_store_cls=output_cls,
                                return_value=output,
                            )
                        except PersistentStorageException:
                            pass

                class_test_id_list = [
                    cls.__name__,
                    cls._test_identifier(casex.cassette),
                ]
                for position in range(len(args)):
                    output = int_dec_fn(args[position], class_test_id_list + [position])
                for k, v in kwargs.items():
                    output = int_dec_fn(v, class_test_id_list + [k])
                return output

            return store_files_int

        casex.function = internal
        return casex

    @classmethod
    def where_arg_references(
        cls,
        key_position_params_dict: Dict,
        cassette: Optional[Cassette] = None,
        output_cls: Optional[Any] = None,
    ) -> Any:
        """
        Decorator what will store files or directory based on arguments,
        you have to pass name and position of arg via dict
        (be careful about counting self or cls parameteres for methods)
        eg. key_position_params_dict = {"target_dir": 2}

        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """
        casex, output_cls = cls.__get_executor_and_return_cls(cassette, output_cls)

        def internal(func):
            @functools.wraps(func)
            def store_files_int_int(*args, **kwargs):
                output = None
                class_test_id_list = [
                    cls.__name__,
                    cls._test_identifier(casex.cassette),
                ]
                if casex.cassette.mode != StorageMode.read:
                    output = func(*args, **kwargs)
                for key, position in key_position_params_dict.items():
                    if key in kwargs:
                        param = kwargs[key]
                    else:
                        param = args[position]
                    output = cls._copy_logic(
                        cassette=casex.cassette,
                        pathname=param,
                        keys=class_test_id_list + [key],
                        ret_store_cls=output_cls,
                        return_value=output,
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
        output_cls: Optional[Any] = None,
    ) -> Any:
        """
        Method to store explicitly path file_param to persistent storage

        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """
        casex, output_cls = cls.__get_executor_and_return_cls(cassette, output_cls)

        def internal(func):
            @functools.wraps(func)
            def store_files_int(*args, **kwargs):
                output = None
                class_test_id_list = [
                    cls.__name__,
                    cls._test_identifier(casex.cassette),
                ]
                if casex.cassette.mode != StorageMode.read:
                    output = func(*args, **kwargs)
                output = cls._copy_logic(
                    cassette=casex.cassette,
                    pathname=file_param,
                    keys=class_test_id_list + [dest_key],
                    ret_store_cls=output_cls,
                    return_value=output,
                )
                return output

            return store_files_int

        casex.function = internal
        return casex

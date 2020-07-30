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
import inspect
import logging
import pickle
import warnings
from typing import Optional, Callable, Any, List, Dict

from requre.storage import PersistentObjectStorage
from requre.cassette import (
    original_time,
    StorageKeysInspectFull,
    Cassette,
    CassetteExecution,
)


logger = logging.getLogger(__name__)


class ObjectStorage:
    """
    Generic object API for objects for persistent storage.
    Use it as parent class for your custom object handling

    This class use pickle module for object serialization,
    it is generic, but may lead to some issues
    in case object is not serializable well. Use this class very carefully.
    """

    _cassette: Cassette = None
    __response_keys: list = list()
    object_type = object

    def __init__(
        self,
        store_keys: list,
        cassette: Cassette,
        storage_object_kwargs: Optional[dict] = None,
    ) -> None:
        self.store_keys = store_keys
        if cassette:
            self.set_cassette(cassette)
        self.store_keys = store_keys
        self.storage_object_kwargs = storage_object_kwargs or {}

    @classmethod
    def get_cassette(cls):
        """
        Internal method to return proper cassette, it is important after rewriting of singletons
        Cassette were not passed to object executor
        :return: Cassette instance
        """
        if cls._cassette:
            return cls._cassette
        else:
            return PersistentObjectStorage().cassette

    @classmethod
    def set_cassette(cls, value):
        cls._cassette = value

    @classmethod
    def get_base_keys(cls, func: Callable) -> List[Any]:
        function = func.function if isinstance(func, CassetteExecution) else func
        return cls.get_cassette().data_miner.key_stategy_cls.get_base_keys(function)

    @classmethod
    def execute(
        cls,
        keys: list,
        func: Callable,
        *args,
        storage_object_kwargs=None,
        cassette: Cassette,
        **kwargs,
    ) -> Any:
        """
        Class method to store or read object from persistent storage
        with explicit set of *args, **kwargs parameters to use as keys
        :param keys: list of keys used as parameter
        :param func: original function
        :param args: parameters of original function
        :param storage_object_kwargs: forwarded to the storage object
        :param cassette: Cassette instance to pass inside object to work with
        :param kwargs: parameters of original function
        :return: CassetteExecution class with function and cassette instance
        """
        storage_object_kwargs = storage_object_kwargs or {}
        object_storage = cls(
            store_keys=keys, cassette=cassette, **storage_object_kwargs
        )

        if object_storage.get_cassette().do_store(keys):
            time_before = original_time()
            func_exposed = (
                func.function if isinstance(func, CassetteExecution) else func
            )
            response = func_exposed(*args, **kwargs)

            time_after = original_time()
            metadata: Dict = {
                cassette.data_miner.LATENCY_KEY: time_after - time_before,
                cassette.data_miner.METADATA_CALLER_LIST: StorageKeysInspectFull.get_base_keys(
                    func_exposed
                ),
            }
            if cassette.data_miner.store_arg_debug_metadata:
                args_clean = [f"'{x}'" if isinstance(x, str) else str(x) for x in args]
                kwargs_clean = [
                    f"""{k}={f"'{v}'" if isinstance(v, str) else str(v)}"""
                    for k, v in kwargs.items()
                ]
                caller = (
                    f"{func_exposed.__name__}({', '.join(args_clean + kwargs_clean)})"
                )
                metadata[cassette.data_miner.METADATA_ARG_DEBUG_KEY] = caller
            object_storage.write(response, metadata)
            logger.debug(f"WRITE Keys: {keys} -> {response}")
            return response

        else:
            response = object_storage.read()
            logger.debug(f"READ  Keys: {keys} -> {response}")
            return response

    @classmethod
    def execute_all_keys(
        cls,
        func: Callable,
        *args,
        storage_object_kwargs=None,
        cassette: Cassette,
        **kwargs,
    ):
        """
        Class method what does same as execute, but use all *args, **kwargs as keys
        :param func: original function
        :param args: parameters of original function
        :param storage_object_kwargs: forwarded to the storage object
        :param kwargs: parameters of original function
        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """
        func_exposed = func.function if isinstance(func, CassetteExecution) else func
        keys = (
            cls.get_base_keys(func_exposed)
            + [x for x in args if isinstance(int, str)]
            + [f"{k}:{v}" for k, v in kwargs.items()]
        )
        return cls.execute(
            keys,
            func,
            *args,
            storage_object_kwargs=storage_object_kwargs,
            cassette=cassette,
            **kwargs,
        )

    @classmethod
    def execute_plain(
        cls,
        func: Callable,
        *args,
        storage_object_kwargs=None,
        cassette: Cassette,
        **kwargs,
    ):
        """
        Class method what does same as execute, but use just name of module and function as name

        :param func: original function
        :param args: parameters of original function
        :param storage_object_kwargs: forwarded to the storage object
        :param kwargs: parameters of original function
        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """
        func_exposed = func.function if isinstance(func, CassetteExecution) else func
        keys = cls.get_base_keys(func_exposed)
        return cls.execute(
            keys,
            func,
            *args,
            storage_object_kwargs=storage_object_kwargs,
            cassette=cassette,
            **kwargs,
        )

    @classmethod
    def decorator_all_keys(
        cls, storage_object_kwargs=None, cassette: Cassette = None
    ) -> Any:
        """
        Class method for what should be used as decorator of import replacing system
        This use all arguments of function as keys

        :param func: Callable object
        :param storage_object_kwargs: forwarded to the storage object
        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """

        def internal(func):
            @functools.wraps(func)
            def internal_internal(*args, **kwargs):
                return cls.decorator(
                    item_list=list(range(len(args))) + list(kwargs.keys()),
                    cassette=cassette,
                )(func)(*args, **kwargs)

            return internal_internal

        return internal

    @classmethod
    def decorator(
        cls,
        *,
        item_list: list,
        map_function_to_item=None,
        storage_object_kwargs=None,
        cassette: Cassette = None,
    ) -> Any:
        """
        Class method for what should be used as decorator of import replacing system
        This use list of selection of *args or **kwargs as arguments of function as keys

        :param item_list: list of values of *args nums,  **kwargs names to use as keys
        :param map_function_to_item: dict of function to apply to keys before storing
                                  (have to be listed in item_list)
        :param storage_object_kwargs: forwarded to the storage object
        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance
        """

        map_function_to_item = map_function_to_item or {}
        casex = CassetteExecution()
        casex.cassette = cassette or cls.get_cassette()
        casex.obj_cls = cls

        def internal(func: Callable):
            @functools.wraps(func)
            def internal_internal(*args, **kwargs):
                keys = cls.get_base_keys(func)
                # get all possible arguments of passed function
                try:
                    arg_keys = inspect.getfullargspec(func)[0]
                except TypeError:
                    arg_keys = []
                for param_name in item_list:
                    # if you pass int as an agrument, it forces to use args
                    if isinstance(param_name, int):
                        key = args[param_name]
                    # try to look into kwargs if item is there
                    elif param_name in kwargs:
                        key = kwargs[param_name]
                    #  translate param name to positional argument
                    else:
                        # out of index check. This is bad but possible use case
                        # raise warning and continue
                        if len(args) <= arg_keys.index(param_name):
                            warnings.warn(
                                f"You've defined keys: {item_list} but '{param_name}' is not part"
                                f" of args:{args} and kwargs:{kwargs},"
                                f" original function and args: {func.__name__}({arg_keys})"
                            )
                            # but add there None as key, to not spoil dictionary deep
                            key = None
                        else:
                            key = args[arg_keys.index(param_name)]
                    if param_name not in map_function_to_item:
                        keys.append(key)
                    else:
                        keys.append(map_function_to_item[param_name](key))
                return cls.execute(
                    keys,
                    func,
                    *args,
                    storage_object_kwargs=storage_object_kwargs,
                    cassette=casex.cassette,
                    **kwargs,
                )

            return internal_internal

        casex.function = internal
        return casex

    @classmethod
    def decorator_plain(
        cls, *, cassette: Cassette = None, storage_object_kwargs=None
    ) -> Any:
        return cls.decorator(
            item_list=[], cassette=cassette, storage_object_kwargs=storage_object_kwargs
        )

    def write(self, obj: Any, metadata: Optional[Dict] = None) -> Any:
        """
        Write the object representation to storage
        Internally it will use self.to_serializable
        method to get serializable object representation

        :param obj: some object
        :param metadata: store metedata to object
        :return: same obj
        """
        self.get_cassette().store(
            self.store_keys, self.to_serializable(obj), metadata=metadata
        )
        return obj

    def read(self):
        """
        Crete object representation of serialized data in persistent storage
        Internally it will use self.from_serializable method transform object

        :return: proper object
        """
        data = self.get_cassette()[self.store_keys]
        obj = self.from_serializable(data)
        return obj

    def to_serializable(self, obj: Any) -> Any:
        """
        Internal method for object serialization

        :param obj: some object
        :return: Yaml serializable object
        """
        output = pickle.dumps(obj)
        return output

    def from_serializable(self, data: Any) -> Any:
        """
        Internal method for object de-serialization

        :param data: Yaml serializable object
        :return: some object
        """
        output = pickle.loads(data)
        return output

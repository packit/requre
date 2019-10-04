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
from typing import Optional, Callable, Any, List

from requre.storage import PersistentObjectStorage
from requre.utils import STORAGE


class ObjectStorage:
    """
    Generic object API for objects for persistent storage.
    Use it as parent class for your custom object handling

    This class use pickle module for object serialization,
    it is generic, but may lead to some issues
    in case object is not serializable well. Use this class very carefully.
    """

    persistent_storage = STORAGE
    __response_keys: list = list()
    object_type = object

    def __init__(
        self, store_keys: list, pstorage: Optional[PersistentObjectStorage] = None
    ) -> None:
        self.store_keys = store_keys
        if pstorage:
            self.persistent_storage = pstorage
        self.store_keys = store_keys

    @staticmethod
    def __get_base_keys(func: Callable) -> List[Any]:
        output: List[str] = list()
        # callers module list, to be able to separate requests for various services in one file
        caller_list: List[str] = list()
        for currnetframe in inspect.stack():
            module_name = inspect.getmodule(currnetframe[0]).__name__
            if module_name.startswith("_"):
                break
            else:
                if len(caller_list) and caller_list[-1] == module_name:
                    continue
                else:
                    caller_list.append(module_name)
        output += caller_list[::-1]
        # module name where function is
        output.append(inspect.getmodule(func).__name__)
        # name of function what were used
        output.append(func.__name__)
        return output

    @classmethod
    def execute(cls, keys: list, func: Callable, *args, **kwargs) -> Any:
        """
        Class method to store or read object from persistent storage
        with explicit set of *args, **kwargs parameters to use as keys
        :param keys: list of keys used as parameter
        :param func: original function
        :param args: parameters of original function
        :param kwargs: parameters of original function
        :return: output of called func
        """
        logger = logging.getLogger(cls.__name__)
        rrstorage = cls(store_keys=keys)
        if rrstorage.persistent_storage.is_write_mode:
            response = func(*args, **kwargs)
            rrstorage.write(response)
            logger.debug(f"WRITE Keys: {keys} -> {response}")
            return response
        else:
            response = rrstorage.read()
            logger.debug(f"READ  Keys: {keys} -> {response}")
            return response

    @classmethod
    def execute_all_keys(cls, func: Callable, *args, **kwargs):
        """
        Class method what does same as execute, but use all *args, **kwargs as keys
        :param func: original function
        :param args: parameters of original function
        :param kwargs: parameters of original function
        :return: output of called func
        """
        keys = (
            cls.__get_base_keys(func)
            + [x for x in args if isinstance(int, str)]
            + [f"{k}:{v}" for k, v in kwargs.items()]
        )
        return cls.execute(keys, func, *args, **kwargs)

    @classmethod
    def execute_plain(cls, func: Callable, *args, **kwargs):
        """
        Class method what does same as execute, but use just name of module and function as name

        :param func: original function
        :param args: parameters of original function
        :param kwargs: parameters of original function
        :return: output of called func
        """
        keys = cls.__get_base_keys(func)
        return cls.execute(keys, func, *args, **kwargs)

    @classmethod
    def decorator_all_keys(cls, func: Callable) -> Any:
        """
        Class method for what should be used as decorator of import replacing system
        This use all arguments of function as keys

        :param func: Callable object
        :return: output of func
        """

        @functools.wraps(func)
        def internal(*args, **kwargs):
            return cls.execute_all_keys(func, *args, **kwargs)

        return internal

    @classmethod
    def decorator(cls, *, item_list: list) -> Any:
        """
        Class method for what should be used as decorator of import replacing system
        This use list of selection of *args or **kwargs as arguments of function as keys

        :param func: Callable object
        :param item_list: list of values of *args nums,  **kwargs names to use as keys
        :return: output of func
        """

        def internal(func: Callable):
            @functools.wraps(func)
            def internal_internal(*args, **kwargs):
                keys = cls.__get_base_keys(func)
                for item in item_list:
                    if isinstance(item, int):
                        keys.append(args[item])
                    else:
                        keys.append(kwargs[item])
                return cls.execute(keys, func, *args, **kwargs)

            return internal_internal

        return internal

    @classmethod
    def decorator_plain(cls, func: Callable) -> Any:
        """
        Class method for what should be used as decorator of import replacing system
        This use no arguments of function as keys

        :param func: Callable object
        :return: output of func
        """

        @functools.wraps(func)
        def internal(*args, **kwargs):
            return cls.execute_plain(func, *args, **kwargs)

        return internal

    def write(self, obj: Any) -> Any:
        """
        Write the object representation to storage
        Internally it will use self.to_serializable()
        method to get serializable object representation

        :param obj: some object
        :return: same obj
        """
        self.persistent_storage.store(self.store_keys, self.to_serializable(obj))
        return obj

    def read(self):
        """
        Crete object representation of serialized data in persistent storage
        Internally it will use self.from_serializable method transform object

        :return: proper object
        """
        data = self.persistent_storage.read(self.store_keys)
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

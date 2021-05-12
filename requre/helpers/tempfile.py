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
import functools
import logging
from typing import Optional, Any, Callable
from requre.cassette import Cassette, CassetteExecution
from requre.objects import ObjectStorage
from requre.helpers.simple_object import Simple
from warnings import warn

logger = logging.getLogger(__name__)


class MkTemp(Simple):
    """
    decorate mktemp method wrapper
    """

    root = "/tmp/static_tmp"

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
        storage_object_kwargs = storage_object_kwargs or {}
        object_storage = cls(
            store_keys=keys, cassette=cassette, **storage_object_kwargs
        )

        base_prefix = os.path.join(
            cls.root, os.path.basename(object_storage.get_cassette().storage_file)
        )
        os.makedirs(os.path.dirname(base_prefix), exist_ok=True)
        current = 0
        if os.path.exists(base_prefix):
            with open(base_prefix) as fd:
                current = int(fd.read())
        current += 1
        with open(base_prefix, mode="w") as fd:
            fd.write(f"{current}")
        path = f"{base_prefix}_{current}"
        return path


class MkDTemp(MkTemp):
    """
    decorate mkdtemp method wrapper
    """

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
        path = super().execute(keys, func, *args, cassette=cassette, **kwargs)
        os.makedirs(path, exist_ok=True)
        return path


class TempFile(ObjectStorage):
    """
    replace system tempfile module with own predictable names implementation
     of temp files for mocking

     Warn: Replaced by new implementations MkDTemp and MkTemp classes
    """

    root = "/tmp"
    prefix = "static_tmp"
    _cassette: Cassette = None
    _cassette_file = None
    counter = 0
    dir_suffix = "file_storage"

    @classmethod
    def set_cassette(cls, value: Cassette):
        if value.storage_file != cls._cassette_file:
            # cassette file may be same, but storage file could change,
            # be avare of that in case of counter
            cls._cassette_file = value.storage_file
            cls.counter = 0
        cls._cassette = value

    @classmethod
    def next(cls):
        cls.counter += 1
        return cls.counter

    @classmethod
    def _get_name(cls, prefix: Optional[str] = None) -> str:
        if not cls._cassette:
            cls._cassette = cls.get_cassette()
        cls.set_cassette(cls._cassette)
        filename = os.path.join(
            cls.root,
            os.path.basename(cls.get_cassette().storage_file),
            f"{prefix or cls.prefix}_{cls.next()}",
        )
        os.makedirs(os.path.dirname(filename), mode=0o777, exist_ok=True)
        logger.debug(f"Use name for tempfile: ${filename}")
        return filename

    @classmethod
    def mktemp(cls, cassette: Optional[Cassette] = None) -> Any:
        """
        Decorator what will store return value of function/method as file and will store content

        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance

        """
        warn("Please replace it by MkTemp.decorator_plain()")
        casex = CassetteExecution()
        casex.cassette = cassette or cls.get_cassette()
        casex.obj_cls = cls

        def internal(func):
            @functools.wraps(func)
            def __mktemp(*args, **kwargs):
                output = cls._mktemp(*args, **kwargs)
                return output

            return __mktemp

        casex.function = internal
        return casex

    @classmethod
    def mkdtemp(cls, cassette: Optional[Cassette] = None) -> Any:
        """
        Decorator what will store return value of function/method as file and will store content

        :param cassette: Cassette instance to pass inside object to work with
        :return: CassetteExecution class with function and cassette instance

        """
        warn("Please replace it by class mkdtemp MkDTemp.decorator_plain()")
        casex = CassetteExecution()
        casex.cassette = cassette or cls.get_cassette()
        casex.obj_cls = cls

        def internal(func):
            @functools.wraps(func)
            def __mkdtemp(*args, **kwargs):
                output = cls._mkdtemp(*args, **kwargs)
                return output

            return __mkdtemp

        casex.function = internal
        return casex

    @classmethod
    def _mktemp(cls, prefix: Optional[str] = None) -> str:
        return cls._get_name(prefix)

    @classmethod
    def _mkdtemp(cls, prefix: Optional[str] = None) -> str:
        name = cls._get_name(prefix)
        os.makedirs(name)
        return name

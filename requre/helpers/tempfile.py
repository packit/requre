# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import functools
import logging
import os
from typing import Any, Optional
from warnings import warn

from requre.cassette import Cassette, CassetteExecution
from requre.objects import ObjectStorage
from requre.record_and_replace import (
    make_generic,
    replace_module_match_with_multiple_decorators,
)
from requre.simple_object import Simple

logger = logging.getLogger(__name__)


class MkTemp(Simple):
    """
    decorate mktemp method wrapper
    """

    pass


class MkDTemp(Simple):
    """
    decorate mkdtemp method wrapper
    """

    def from_serializable(self, data: Any) -> Any:
        os.makedirs(data, exist_ok=True)
        return data


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


@make_generic
def record_tempfile_module(
    _func=None,
    cassette: Optional[Cassette] = None,
):
    """Records tempfile.mkdtemp and tempfile.mktemp calls."""
    decorators = [
        ("tempfile.mkdtemp", MkDTemp.decorator_plain()),
        ("tempfile.mktemp", MkTemp.decorator_plain()),
    ]
    record_tempfile_decorator = replace_module_match_with_multiple_decorators(
        *decorators,
        cassette=cassette,
    )

    if _func is not None:
        return record_tempfile_decorator(_func)
    else:
        return record_tempfile_decorator

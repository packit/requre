import functools
import logging
import os
import re
from contextlib import contextmanager
from typing import List, Callable, Optional, Dict, Any, Union

import sys

from requre.cassette import Cassette
from requre.helpers.requests_response import (
    RequestResponseHandling,
    remove_password_from_url,
)
from requre.objects import ObjectStorage
from requre.storage import PersistentObjectStorage
from requre.storage import (
    StorageKeysInspectSimple,
    DataMiner,
)
from requre.utils import get_datafile_filename

logger = logging.getLogger(__name__)


def replace(
    in_module: str,
    what: str,
    decorate: Optional[Callable] = None,
    replace: Optional[Callable] = None,
    storage_file: Optional[str] = None,
):
    if (decorate is None and replace is None) or (
        decorate is not None and replace is not None
    ):
        raise ValueError("right one from [decorate, replace] parameter has to be set.")

    def decorator_cover(func):
        @functools.wraps(func)
        def _internal(*args, **kwargs):
            original_storage = None
            if storage_file:
                original_storage = PersistentObjectStorage().storage_file
                PersistentObjectStorage().storage_file = storage_file
            original_module_items: Dict[List] = {}
            for module_name, module in sys.modules.items():
                if not re.search(in_module, module_name):
                    continue
                logger.info(f"\nMATCHED MODULE: {module_name} by {in_module}")

                if len(what) > 0:
                    original_obj = module
                    parent_obj = original_obj
                    # trace into object structyre and get these objects
                    for key_item in what.split("."):
                        parent_obj = original_obj
                        original_obj = getattr(original_obj, key_item)
                    if replace is not None:
                        setattr(
                            parent_obj, original_obj.__name__, replace,
                        )
                        logger.info(
                            f"\treplacing {module_name}.{what}"
                            f" by function {replace.__name__}"
                        )
                    elif decorate is not None:
                        setattr(
                            parent_obj, original_obj.__name__, decorate(original_obj),
                        )
                        logger.info(
                            f"\tdecorating {module_name}.{what}"
                            f" by function {decorate.__name__}"
                        )
                    original_module_items[module_name] = [
                        what,
                        parent_obj,
                        original_obj,
                    ]
                else:
                    raise ValueError(
                        "You have to define what will be replaced inside module,"
                        " not possible to replace whole module on the fly"
                    )
            # execute content

            output = func(*args, **kwargs)

            # revert back
            for module_name, item_list in original_module_items.items():
                setattr(item_list[1], item_list[2].__name__, item_list[2])
            if original_storage:
                PersistentObjectStorage().storage_file = original_storage
            return output

        return _internal

    return decorator_cover


def _parse_and_replace_sys_modules(
    what: str, decorate: Any = None, replace: Any = None,
) -> Dict:
    """
    Internal fucntion what will check all sys.modules, and try to find there implementation of
    "what" and replace or decorate it by given value(s)
    """
    logger.info(f"\n++++++ SEARCH {what} decorator={decorate} replace={replace}")
    original_module_items: Dict[str, Dict] = {}
    # go over all modules, and try to find match
    for module_name, module in sys.modules.items():
        full_module_list = what.split(".")
        # avoid to deep dive into
        # if not matched, try to find just part, if not imported as full path
        for depth, _ in enumerate(full_module_list):
            original_obj = module
            parent_obj = None
            # rest of list has to match object path
            for module_path in full_module_list[depth:]:
                parent_obj = original_obj
                try:
                    original_obj = getattr(original_obj, module_path)
                except AttributeError:
                    # this is used also for indication that match of path passed
                    # in case it match partial path, make it None
                    parent_obj = None
                    break
                original_obj_text = (
                    original_obj.__name__
                    if hasattr(original_obj, "__name__")
                    else str(original_obj)
                )
                logger.debug(
                    f"\tmodule {module_name} -> {module_path} in "
                    f"{original_obj_text} ({full_module_list[depth:]})"
                )
            # continue if parent is empty or module of function did not match
            # path inside what avoid replace something else with same path
            # eg, you define what "re.search", and it matches "search" as
            # part of your module but it does not come from re module

            try:
                # TODO: this part should be improved, theoretically
                #  join(full_module_list).startswith( original_obj.__module__)
                #  could lead to issue, that it matches another module path
                if not parent_obj:
                    continue
                if not ".".join(full_module_list).startswith(original_obj.__module__):
                    logger.debug(
                        f"SIMILAR MATCH module {module_name} "
                        f"in {parent_obj.__name__} -> {original_obj.__name__} "
                        f"from {original_obj.__module__} ({full_module_list[depth:]})"
                    )
                    continue
            except AttributeError as e:
                logger.debug(e)
                continue
            logger.info(
                f"MATCH module {module_name} "
                f"in {parent_obj.__name__} -> {original_obj.__name__} "
                f"from {original_obj.__module__} ({full_module_list[depth:]})"
            )
            if replace is not None:
                new_function = replace
                replacement = new_function
            elif decorate is not None:
                new_function = decorate
                if isinstance(new_function, list):
                    replacement = original_obj
                    for item in new_function:
                        replacement = item(replacement)
                else:
                    replacement = new_function(original_obj)
            else:
                continue
            # check if already replaced, then continue
            if original_obj in [
                x["replacement"] for x in original_module_items.values()
            ]:
                logger.info(f"\talready replaced {what} in {module_name}")
                continue
            # TODO: have to try to investigate how to do multiple replacements of same
            #  change the module string in replacements, to be able to do multiple
            #  replacements this is tricky and may be confusing, but also make it
            #  clear what has to be replaced
            #  replacement.__module__ = original_obj.__module__
            setattr(
                parent_obj, original_obj.__name__, replacement,
            )
            fn_str = (
                new_function.__name__
                if not isinstance(new_function, list)
                else new_function
            )
            logger.info(
                f"\tREPLACES {what} in {module_name}"
                f" by function {fn_str} {original_obj}"
            )
            original_module_items[module_name] = {
                "what": what,
                "parent_obj": parent_obj,
                "original_obj": original_obj,
                "replacement": replacement,
            }
    return original_module_items


def _change_storage_file(storage_file, func, args):
    """
    Internal function that try to construct persistent data file based on various
    possibilities.
    """
    if storage_file:
        PersistentObjectStorage().storage_file = storage_file
    else:

        if len(args):
            try:
                PersistentObjectStorage().storage_file = get_datafile_filename(args[0])
            except NameError:
                PersistentObjectStorage().storage_file = get_datafile_filename(func)
        else:
            PersistentObjectStorage().storage_file = get_datafile_filename(func)
    original_storage_file = PersistentObjectStorage().storage_file
    return original_storage_file


def replace_module_match(
    what: str,
    decorate: Optional[Union[List[Callable], Callable]] = None,
    replace: Optional[Callable] = None,
    storage_file: Optional[str] = None,
    storage_keys_strategy=StorageKeysInspectSimple,
):
    """
    Decorator what helps you to replace/decorate functions/methods inside any already
    imported module. It uses what as identifier what you want to replace, then you can
    define if it will be decorated or replaced by given function.

    Be aware of several situations:
      * This will not work if there are dynamic imports inside code execution
        * Workaround: import the module as part of your test code fist
      * When you try to decorate/replace method what is not defined (e.g. via using __getattr__)
        * Workaround: try it. maybe it will work as expected.
        Import the module and create there mock the method, or replace it with inspired by
        __getattr__ codebase

    Example usage to decorate request method of requests module:
    @replace_module_match(what="requests.sessions.Session.request",
                          decorate=RequestResponseHandling.decorator(
                          item_list=["method", "url", "data"],
                          map_item_list={"url": remove_password_from_url})

    :param what: str - full path of function inside module
    :param decorate: function decorator what will be applied to what, could be also list of
                     decorators, to be able to apply more decorators on one function
                     eg. store files and store output
    :param replace: replace original function by given one
    :param storage_file: path for storage file if you don't want to use default location
    :param storage_keys_strategy: you can change key strategy for storing data
                                  default simple one avoid to store stack information
    """
    if (decorate is None and replace is None) or (
        decorate is not None and replace is not None
    ):
        raise ValueError("right one from [decorate, replace] parameter has to be set.")

    def decorator_cover(func):
        @functools.wraps(func)
        def _internal(*args, **kwargs):
            original_key_strategy = DataMiner().key_stategy_cls
            # use simple strategy, to not store stack info as keys
            DataMiner().key_stategy_cls = storage_keys_strategy
            original_storage_file = _change_storage_file(
                storage_file=storage_file, func=func, args=args
            )
            # ensure that directory structure exists already
            os.makedirs(
                os.path.dirname(PersistentObjectStorage().storage_file), exist_ok=True
            )
            # Store values and their replacements for modules to be able to revert changes back
            original_module_items = _parse_and_replace_sys_modules(
                what=what, decorate=decorate, replace=replace
            )
            try:
                # execute content
                output = func(*args, **kwargs)
            except Exception as e:
                raise (e)
            finally:
                # dump data to storage file
                PersistentObjectStorage().dump()
                # revert back changed functions
                for module_name, item_list in original_module_items.items():
                    setattr(
                        item_list["parent_obj"],
                        item_list["original_obj"].__name__,
                        item_list["original_obj"],
                    )
                # revert back changed values of singletons, to go to consistent state before test
                # it is important in this order
                PersistentObjectStorage().storage_file = original_storage_file
                DataMiner().key_stategy_cls = original_key_strategy
            return output

        return _internal

    return decorator_cover


def record(
    what: str, storage_file: Optional[str] = None,
):
    """
    Decorator which can be used to store calls of the function and
    and replay responses on the next run.

    :param what: str - full path of function inside module
    :param storage_file: path for storage file if you don't want to use default location
    """

    def _record_inner(func):
        return replace_module_match(
            what=what,
            decorate=ObjectStorage.decorator_all_keys,
            storage_file=storage_file,
        )(func)

    return _record_inner


def record_requests(
    _func=None, response_headers_to_drop: Optional[List[str]] = None, storage_file=None
):
    """
    Decorator which can be used to store all requests to a file
    and replay responses on the next run.

    - The matching is based on `url`.
    - Removes tokens from the url when saving if needed.

    Can be used with or without parenthesis.

    :param _func: can be used to decorate function (with, or without parenthesis).
    :param response_headers_to_drop: list of header names we don't want to save with response
                                        (Will be replaced to `None`.)
    :param storage_file: file for reading and writing data in storage_object
    """

    response_headers_to_drop = response_headers_to_drop or []

    def decorator_cover(func):
        return replace_module_match(
            what="requests.sessions.Session.request",
            decorate=RequestResponseHandling.decorator(
                item_list=["method", "url"],
                map_function_to_item={"url": remove_password_from_url},
                response_headers_to_drop=response_headers_to_drop,
            ),
            storage_file=storage_file,
        )(func)

    if _func is None:
        return decorator_cover
    else:
        return decorator_cover(_func)


@contextmanager
def recording(
    what: str,
    decorate: Optional[Union[List[Callable], Callable]] = None,
    replace: Optional[Callable] = None,
    storage_file: Optional[str] = None,
    storage_keys_strategy=StorageKeysInspectSimple,
):
    """
    Context manager which can be used to store calls of the function and
    and replay responses on the next run.

    :param what: str - full path of function inside module
    :param decorate: function decorator what will be applied to what, could be also list of
                     decorators, to be able to apply more decorators on one function
                     eg. store files and store output
    :param replace: replace original function by given one
    :param storage_file: path for storage file if you don't want to use default location
    :param storage_keys_strategy: you can change key strategy for storing data
                                  default simple one avoid to store stack information
    """

    original_key_strategy = DataMiner().key_stategy_cls
    DataMiner().key_stategy_cls = storage_keys_strategy
    original_storage_file = storage_file
    PersistentObjectStorage().storage_file = storage_file
    # ensure that directory structure exists already
    os.makedirs(os.path.dirname(PersistentObjectStorage().storage_file), exist_ok=True)
    # Store values and their replacements for modules to be able to revert changes back
    original_module_items = _parse_and_replace_sys_modules(
        what=what, decorate=decorate, replace=replace
    )
    try:
        yield Cassette()
    finally:
        # dump data to storage file
        PersistentObjectStorage().dump()
        # revert back changed functions
        for module_name, item_list in original_module_items.items():
            setattr(
                item_list["parent_obj"],
                item_list["original_obj"].__name__,
                item_list["original_obj"],
            )
        # revert back changed values of singletons, to go to consistent state before test
        # it is important in this order
        PersistentObjectStorage().storage_file = original_storage_file
        DataMiner().key_stategy_cls = original_key_strategy


@contextmanager
def recording_requests(
    response_headers_to_drop: Optional[List[str]] = None, storage_file=None
):
    """
    Context manager which can be used to store all requests to a file
    and replay responses on the next run.

    - The matching is based on `url`.
    - Removes tokens from the url when saving if needed.

    :param _func: can be used to decorate function (with, or without parenthesis).
    :param response_headers_to_drop: list of header names we don't want to save with response
                                        (Will be replaced to `None`.)
    :param storage_file: file for reading and writing data in storage_object
    """
    with recording(
        what="requests.sessions.Session.request",
        decorate=RequestResponseHandling.decorator(
            item_list=["method", "url"],
            map_function_to_item={"url": remove_password_from_url},
            response_headers_to_drop=response_headers_to_drop,
        ),
        storage_file=storage_file,
    ) as cassette:
        yield cassette

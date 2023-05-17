# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import functools
import inspect
import logging
import os
import re
import sys
import types
from contextlib import contextmanager
from typing import Any, Callable, List, Optional, Tuple, Union

from requre.cassette import Cassette, CassetteExecution
from requre.cassette import StorageKeysInspectSimple
from requre.constants import (
    REQURE_CASSETTE_ATTRIBUTE_NAME,
    REQURE_SETUP_APPLIED_ATTRIBUTE_NAME,
    TEST_METHOD_REGEXP,
)
from requre.guess_object import Guess
from requre.utils import get_datafile_filename, get_module_of_previous_context

logger = logging.getLogger(__name__)


class ModuleRecord:
    """
    Store data entry for replacement system, to be able to _revert_modules changes
    back after execution finishes.
    """

    def __init__(self, what, parent, original, replacement, add_revert_list=None):
        self.what = what
        self.parent = parent
        self.original = original
        self.replacement = replacement
        self.add_revert_list = add_revert_list or []
        self.caller_module = get_module_of_previous_context()

    def __str__(self):
        return (
            f"ModuleRecord({self.what}, {self.parent}, {self.original},"
            f" {self.replacement}) {self.caller_module}"
        )


def _apply_module_replacement(
    what,
    module,
    cassette,
    decorate,
    replace,
    module_record_list: List[ModuleRecord],
    add_revert_list: List,
) -> List[ModuleRecord]:
    """
    Internal method what finds inside module if the what string matches.
    If yes, apply the  replacement, otherwise return None

    :param what: What will be replaced
    :param module: the module where we try to find match for "what"
    :param cassette: Cassette instance
    :param decorate: decorator to be applied
    :param replace: replace function to be applied
    :param module_record_list: list of modules what was already applied
    :return: None or ModuleRecord
    """
    full_module_list = what.split(".")
    module_name = module.__name__
    output_record_list: List[ModuleRecord] = list()
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
            if original_obj.__module__ and not ".".join(full_module_list).startswith(
                original_obj.__module__
            ):
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
            if isinstance(replace, CassetteExecution):
                new_function = replace.function
                replace.cassette = cassette
                replace.obj_cls.set_cassette(cassette)
            else:
                new_function = replace
            replacement = new_function
        elif decorate is not None:
            if not isinstance(decorate, list):
                new_function = [decorate]
            else:
                new_function = decorate
            replacement = original_obj
            for item in new_function:
                if isinstance(item, CassetteExecution):
                    item.cassette = cassette
                    item.obj_cls.set_cassette(cassette)
                    replacement = item.function(replacement)
                else:
                    replacement = item(replacement)
        else:
            continue
        # check if already replaced, then continue
        if original_obj in [x.replacement for x in module_record_list]:
            logger.info(f"\talready replaced {what} in {module_name}")
            continue
        # TODO: have to try to investigate how to do multiple replacements of same
        #  change the module string in replacements, to be able to do multiple
        #  replacements this is tricky and may be confusing, but also make it
        #  clear what has to be replaced
        #  replacement.__module__ = original_obj.__module__
        setattr(
            parent_obj,
            original_obj.__name__,
            replacement,
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
        output_record_list.append(
            ModuleRecord(
                what=what,
                parent=parent_obj,
                original=original_obj,
                replacement=replacement,
                add_revert_list=add_revert_list,
            )
        )
    return output_record_list


def _parse_and_replace_sys_modules(
    what: str,
    cassette: Cassette,
    decorate: Any = None,
    replace: Any = None,
    add_revert_list: Optional[List] = None,
) -> List[ModuleRecord]:
    """
    Internal fucntion what will check all sys.modules, and try to find there implementation of
    "what" and replace or decorate it by given value(s)
    """
    logger.info(f"\n++++++ SEARCH {what} decorator={decorate} replace={replace}")
    module_list: List[ModuleRecord] = []
    # go over all modules, and try to find match
    for module in sys.modules.copy().values():
        if not isinstance(module, types.ModuleType):
            # ignore non-modules (for example coverage abuses sys.modules
            # to store its DebugOutputFile object)
            continue
        module_list += _apply_module_replacement(
            what=what,
            module=module,
            cassette=cassette,
            decorate=decorate,
            replace=replace,
            module_record_list=module_list,
            add_revert_list=add_revert_list,
        )
    return module_list


def change_storage_file(
    cassette: Cassette, func, args, storage_file: Optional[str] = None
):
    """
    Internal function that try to construct persistent data file based on various
    possibilities.

    :param cassette: Cassette instance to pass inside object to work with
    """
    if storage_file:
        cassette.storage_file = storage_file
    else:
        if len(args):
            try:
                cassette.storage_file = get_datafile_filename(args[0])
            except NameError:
                cassette.storage_file = get_datafile_filename(func)
        else:
            cassette.storage_file = get_datafile_filename(func)
    original_storage_file = cassette.storage_file
    return original_storage_file


def _revert_modules(module_list: List[ModuleRecord]):
    """
    Revert modules to original functions

    :param module_list: list of modules
    :return:
    """
    for module_info in module_list:
        setattr(
            module_info.parent,
            module_info.original.__name__,
            module_info.original,
        )
        if not module_info.add_revert_list:
            continue
        # revert also items on additional places if necessarry
        for item in module_info.add_revert_list:
            found = False
            main_key = item.split(".")[-1]
            module_key = ".".join(item.split(".")[:-1])
            for module_name, module in sys.modules.copy().items():
                # go through all modules and try to find if item is stored there
                if module_key.startswith(module_name):
                    parent_obj = module
                    try:
                        for key in module_key.lstrip(module_name)[1:].split("."):
                            parent_obj = getattr(parent_obj, key)
                        setattr(
                            parent_obj,
                            main_key,
                            module_info.original,
                        )
                        found = True
                    except AttributeError:
                        pass
            if not found:
                raise AttributeError(
                    "You've want to revert item, but not found anywhere inside loaded modules"
                )


def make_generic(_decorator=None):
    """
    Decorator for decorators to make them applicable both on classes and methods/functions.

    When the decorated decorator is applied on class, it will be applied on methods.
    By default, it applies the decorator to all `test.*` method;
    use `regexp_method_pattern` argument to change it.
    It also triggers `cassette_setup`/`cassette_teardown` method before/after method execution
    to be able to manipulate cassette in a method shared between all test cases.
    (We do not have access to cassette from regular setUp/tearDown method.)


    Decorator make_generic can be used both with and without parenthesis:

    Example:

    @make_generic
    def my_decorator(fce):
        return fce

    @my_decorator
    class ClassA:
        def method_b(self):
            print("Will be decorated.")
        def method_c(self):
            print("Will be decorated.")

    class ClassD:
        @my_decorator
        def method_e(self):
            print("Will be decorated.")


    Warning:
        If you want to use make_generic with decorator accepting key-word arguments,
        to be able to use the final decorator without arguments or without parenthesis,
        use the following trick to correctly apply all decorators:

        @make_generic
        def add_something(_func=None, add=1):
            def decorator_to_return(fce):
                def fce_to_return():
                    return fce() + add

                return fce_to_return

            if _func is None:
                # @add_something()
                return decorator_to_return
            else:
                # @add_something
                return decorator_to_return(_func)

    """

    def make_generic_decorator_cover(decorator):
        def make_generic_decorator(*args, regexp_method_pattern=None, **kwargs):
            is_direct_call = (
                not kwargs
                and not regexp_method_pattern
                and len(args) == 1
                and isinstance(args[0], (type, Callable))
            )

            if not is_direct_call and (args or kwargs):
                # decorator with arguments
                decorate = decorator(*args, **kwargs)
            else:
                # decorator without arguments
                decorate = decorator

            def decorated_decorator(function_or_class):
                if isinstance(function_or_class, type):
                    return apply_decorator_to_all_methods(
                        decorate, regexp_method_pattern=regexp_method_pattern
                    )(function_or_class)
                else:
                    return decorate(function_or_class)

            # To support syntax with and without parentheses
            # for the decorated decorator.
            if is_direct_call:
                # call without parenthesis, the target is in the arguments
                return decorated_decorator(args[0])
            else:
                # call with parenthesis, real target will be applied later
                return decorated_decorator

        return make_generic_decorator

    # To support syntax with and without parentheses of the make_generic itself.
    if _decorator is None:
        # @make_generic()
        return make_generic_decorator_cover
    else:
        # @make_generic
        return make_generic_decorator_cover(_decorator)


@make_generic
def replace(
    what: str,
    cassette: Optional[Cassette] = None,
    decorate: Optional[Union[List[Callable], Callable]] = None,
    replace: Optional[Callable] = None,
    storage_keys_strategy=None,
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
    :param cassette: Cassette instance to pass inside object to work with
    :param storage_keys_strategy: you can change key strategy for storing data
                                  default simple one avoid to store stack information
    """
    storage_keys_strategy = storage_keys_strategy or StorageKeysInspectSimple

    if decorate is None and replace is None:
        logger.info(f"Using default decorator for {what}")
        decorate = Guess.decorator_plain(cassette=cassette)
    elif decorate is not None and replace is not None:
        raise ValueError("right one from [decorate, replace] parameter has to be set.")

    def replace_decorator(func):
        func_cassette = (
            getattr(func, REQURE_CASSETTE_ATTRIBUTE_NAME)
            if hasattr(func, REQURE_CASSETTE_ATTRIBUTE_NAME)
            else None
        )
        cassette_int = cassette or func_cassette or Cassette()

        @functools.wraps(func)
        def _replaced_function(*args, **kwargs):
            # set storage if not set to default one, based on function name
            if cassette_int.storage_file is None:
                change_storage_file(cassette=cassette_int, func=func, args=args)
            cassette_int.data_miner.key_stategy_cls = storage_keys_strategy
            # ensure that directory structure exists already
            os.makedirs(os.path.dirname(cassette_int.storage_file), exist_ok=True)
            # Store values and their replacements for modules
            # to be able to _revert_modules changes back
            module_list = _parse_and_replace_sys_modules(
                what=what, cassette=cassette_int, decorate=decorate, replace=replace
            )
            try:
                # pass current cassette to underneath decorator and do not overwrite if set there
                if (
                    "cassette" in inspect.getfullargspec(func).annotations
                    and inspect.getfullargspec(func).annotations["cassette"] == Cassette
                    and "cassette" not in kwargs
                ):
                    kwargs["cassette"] = cassette_int
                # execute content
                output = func(*args, **kwargs)
            except Exception as e:
                raise (e)
            finally:
                # dump data to storage file
                cassette_int.dump()
                _revert_modules(module_list)
            return output

        setattr(_replaced_function, REQURE_CASSETTE_ATTRIBUTE_NAME, cassette_int)
        return _replaced_function

    return replace_decorator


@make_generic
def record(
    what: str,
    cassette: Optional[Cassette] = None,
):
    """
    Decorator which can be used to store calls of the function and
    and replay responses on the next run.

    Can be applied both on function/method and class.

    When the applied on class, it will be applied on methods.
    By default, it applies the decorator to all `test.*` method;
    use `regexp_method_pattern` argument to change it.
    It also triggers `cassette_setup`/`cassette_teardown` method before/after method execution
    to be able to manipulate cassette in a method shared between all test cases.
    (We do not have access to cassette from regular setUp/tearDown method.)

    If you want to have more options for the recording, use `replace` decorator instead.
    You can tweak the recording process, structure of the saved data
    and also provide your own way how to store side-effects of the function.

    If you want some pre-made record decorators of common use-cases
    (like for git, tempfile or requests) take a look to `requre.helpers.__init__`.
    They take care about the side-effects for you.

    Examples:

    @record(what="tests.data.special_requre_module.random_number")
    class RecordDecoratorForClass(unittest.TestCase):
        def test_random(self):
            random_number = tests.data.special_requre_module.random_number()
            self.assertEqual(random_number, 0.819349292484907)

    class RecordDecoratorForMethod(unittest.TestCase):
        @record(what="tests.data.special_requre_module.random_number")
        def test_random(self):
            random_number = tests.data.special_requre_module.random_number()
            self.assertEqual(random_number, 0.17583106733657616)


    :param what: str - full path of function inside module
    :param cassette: Cassette instance to pass inside object to work with
    """

    def _record_inner(func):
        return replace(what=what, cassette=cassette)(func)

    return _record_inner


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
    cassette = Cassette()
    cassette.storage_file = storage_file
    cassette.data_miner.key_stategy_cls = storage_keys_strategy
    # ensure that directory structure exists already
    os.makedirs(os.path.dirname(cassette.storage_file), exist_ok=True)
    # use default decorator for context manager if not given.
    if decorate is None and replace is None:
        logger.info(f"Using default decorator for {what}")
        decorate = Guess.decorator_plain(cassette=cassette)
    elif decorate is not None and replace is not None:
        raise ValueError("right one from [decorate, replace] parameter has to be set.")
    # Store values and their replacements for modules to be able to _revert_modules changes back
    module_list = _parse_and_replace_sys_modules(
        what=what, cassette=cassette, decorate=decorate, replace=replace
    )
    try:
        yield cassette
    finally:
        # dump data to storage file
        cassette.dump()
        _revert_modules(module_list)


def cassette_setup_and_teardown_decorator(func):
    """
    Decorator that triggers `cassette_setup` method to be run before the test method.
    """
    if hasattr(func, REQURE_SETUP_APPLIED_ATTRIBUTE_NAME):
        return func

    func_cassette = (
        getattr(func, REQURE_CASSETTE_ATTRIBUTE_NAME)
        if hasattr(func, REQURE_CASSETTE_ATTRIBUTE_NAME)
        else None
    )
    cassette_int = func_cassette or Cassette()

    @functools.wraps(func)
    def cassette_setup_inner(self, *args, **kwargs):
        if hasattr(self, "cassette_setup"):
            self.cassette_setup(cassette=cassette_int)

        if (
            "cassette" in inspect.getfullargspec(func).annotations
            and inspect.getfullargspec(func).annotations["cassette"] == Cassette
            and "cassette" not in kwargs
        ):
            kwargs["cassette"] = cassette_int

        return_value = func(self, *args, **kwargs)

        if hasattr(self, "cassette_teardown"):
            self.cassette_teardown(cassette=cassette_int)

        return return_value

    setattr(cassette_setup_inner, REQURE_CASSETTE_ATTRIBUTE_NAME, cassette_int)
    setattr(cassette_setup_inner, REQURE_SETUP_APPLIED_ATTRIBUTE_NAME, True)
    return cassette_setup_inner


def apply_decorators_recursively_to_fn(decorator_list, func):
    if not decorator_list:
        return func
    recursive_result = apply_decorators_recursively_to_fn(decorator_list[:-1], func)
    return decorator_list[-1](recursive_result)


def apply_decorator_to_all_methods(*decorator: Callable, regexp_method_pattern=None):
    """
    This function works as class decorator and apply decorator to
    all matched methods via regexp (`test.*` by default),
    primary usage is to use it for unittest testcases.

    ref: https://stackoverflow.com/a/6307868

    Also triggers `cassette_setup`/`cassette_teardown` method before/after method execution
    to be able to manipulate cassette in a method shared between all test cases.
    (We do not have access to cassette from regular setUp/tearDown method.)
    """
    regexp_method_pattern = regexp_method_pattern or TEST_METHOD_REGEXP

    # append cassette setup and teardown if exist
    decorator += (cassette_setup_and_teardown_decorator,)

    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and re.match(regexp_method_pattern, attr):
                setattr(
                    cls,
                    attr,
                    apply_decorators_recursively_to_fn(
                        decorator_list=decorator, func=getattr(cls, attr)
                    ),
                )
        return cls

    return decorate


def replace_module_match_with_multiple_decorators(
    *decorators: Tuple[str, Callable],
    cassette: Optional[Cassette] = None,
):
    if not decorators:
        raise AttributeError("decorators parameter has to be defined")
    decorator_list = []
    for what, decorate in decorators:
        decorator_list.append(replace(what=what, decorate=decorate, cassette=cassette))

    def decorator(func):
        return apply_decorators_recursively_to_fn(decorator_list, func)

    return decorator

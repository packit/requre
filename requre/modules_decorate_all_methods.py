from typing import Callable, Optional, Tuple
from requre.online_replacing import (
    replace_module_match,
    apply_decorator_to_all_methods,
    record_requests_for_all_methods,
)
from requre.helpers.tempfile import TempFile
from requre.cassette import Cassette
from requre.constants import TEST_METHOD_REGEXP
from requre.helpers.git.repo import Repo
from requre.helpers.git.fetchinfo import FetchInfoStorageList
from requre.helpers.git.pushinfo import PushInfoStorageList
from requre.helpers.files import StoreFiles

# to keep backward compatibility and use consistent naming
record_requests_module = record_requests_for_all_methods


def __replace_module_match_with_multiple_decorators(
    *decorators: Tuple[str, Callable],
    _func=None,
    cassette: Optional[Cassette] = None,
    regexp_method_pattern=TEST_METHOD_REGEXP,
):
    if not decorators:
        raise AttributeError("decorators parameter has to be defined")
    decorator_list = []
    for what, decorate in decorators:
        decorator_list.append(
            replace_module_match(what=what, decorate=decorate, cassette=cassette)
        )
    if _func is None:
        return apply_decorator_to_all_methods(
            *decorator_list,
            regexp_method_pattern=regexp_method_pattern,
        )

    return apply_decorator_to_all_methods(
        *decorator_list,
        regexp_method_pattern=regexp_method_pattern,
    )(_func)


def record_tempfile_module(
    _func=None,
    cassette: Optional[Cassette] = None,
    regexp_method_pattern=TEST_METHOD_REGEXP,
):
    decorators = [
        ("tempfile.mkdtemp", TempFile.mkdtemp()),
        ("tempfile.mktemp", TempFile.mktemp()),
    ]
    return __replace_module_match_with_multiple_decorators(
        *decorators,
        _func=_func,
        cassette=cassette,
        regexp_method_pattern=regexp_method_pattern,
    )


def record_git_module(
    _func=None,
    cassette: Optional[Cassette] = None,
    regexp_method_pattern=TEST_METHOD_REGEXP,
):
    decorators = [
        (
            "git.repo.base.Repo.clone_from",
            StoreFiles.where_arg_references(
                key_position_params_dict={"to_path": 2},
                return_decorator=Repo.decorator_plain,
                cassette=cassette,
            ),
        ),
        ("git.remote.Remote.push", PushInfoStorageList.decorator_plain()),
        ("git.remote.Remote.fetch", FetchInfoStorageList.decorator_plain()),
        ("git.remote.Remote.pull", FetchInfoStorageList.decorator_plain()),
    ]
    return __replace_module_match_with_multiple_decorators(
        *decorators,
        _func=_func,
        cassette=cassette,
        regexp_method_pattern=regexp_method_pattern,
    )

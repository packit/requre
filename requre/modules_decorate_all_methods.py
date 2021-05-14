from typing import Callable, Optional, Tuple

from requre.cassette import Cassette
from requre.helpers.files import StoreFiles
from requre.helpers.git.fetchinfo import FetchInfoStorageList
from requre.helpers.git.pushinfo import PushInfoStorageList
from requre.helpers.git.repo import Repo
from requre.helpers.tempfile import MkDTemp, MkTemp
from requre.online_replacing import (
    apply_decorators_recursively_to_fn,
    make_generic,
    record_requests_for_all_methods,
    replace_module_match,
)

# to keep backward compatibility and use consistent naming
record_requests_module = record_requests_for_all_methods


def __replace_module_match_with_multiple_decorators(
    *decorators: Tuple[str, Callable],
    cassette: Optional[Cassette] = None,
):
    if not decorators:
        raise AttributeError("decorators parameter has to be defined")
    decorator_list = []
    for what, decorate in decorators:
        decorator_list.append(
            replace_module_match(what=what, decorate=decorate, cassette=cassette)
        )

    def decorator(func):
        return apply_decorators_recursively_to_fn(decorator_list, func)

    return decorator


@make_generic
def record_tempfile_module(
    cassette: Optional[Cassette] = None,
):
    decorators = [
        ("tempfile.mkdtemp", MkDTemp.decorator_plain()),
        ("tempfile.mktemp", MkTemp.decorator_plain()),
    ]
    return __replace_module_match_with_multiple_decorators(
        *decorators,
        cassette=cassette,
    )


@make_generic
def record_git_module(
    cassette: Optional[Cassette] = None,
):
    decorators = [
        (
            "git.repo.base.Repo.clone_from",
            StoreFiles.where_arg_references(
                key_position_params_dict={"to_path": 2},
                output_cls=Repo,
                cassette=cassette,
            ),
        ),
        (
            "git.remote.Remote.push",
            PushInfoStorageList.decorator_plain(),
        ),
        ("git.remote.Remote.fetch", FetchInfoStorageList.decorator_plain()),
        ("git.remote.Remote.pull", FetchInfoStorageList.decorator_plain()),
    ]
    return __replace_module_match_with_multiple_decorators(
        *decorators,
        cassette=cassette,
    )

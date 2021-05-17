# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional

from requre.cassette import Cassette
from requre.helpers.files import StoreFiles
from requre.helpers.git.fetchinfo import FetchInfoStorageList
from requre.helpers.git.pushinfo import PushInfoStorageList
from requre.helpers.git.repo import Repo
from requre.record_and_replace import (
    make_generic,
    replace_module_match_with_multiple_decorators,
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
    return replace_module_match_with_multiple_decorators(
        *decorators,
        cassette=cassette,
    )

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Any
from git.repo.base import Repo as RepoOrigin
from requre.objects import ObjectStorage


class Repo(ObjectStorage):
    store_items = [
        "git_dir",
        "working_dir",
        "_working_tree_dir",
        "_common_dir",
        "_bare",
    ]

    def to_serializable(self, obj: RepoOrigin) -> Any:
        output = dict()
        for item in self.store_items:
            output[item] = getattr(obj, item)
        return output

    def from_serializable(self, data: Any) -> Any:
        out = RepoOrigin(data[self.store_items[0]])
        for item in self.store_items:
            setattr(out, item, data[item])
        return out

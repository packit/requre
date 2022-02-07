# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Any
from io import BytesIO
from git import Commit
from git.repo.base import Repo
from requre.objects import ObjectStorage


class CommitInfo(ObjectStorage):
    def to_serializable(self, obj: Any) -> Any:
        stream = BytesIO()
        obj._serialize(stream)
        stream.flush()
        value = stream.getvalue()
        return [obj.repo.git_dir, obj.binsha, value]

    def from_serializable(self, data: Any) -> Any:
        commit = Commit(repo=Repo.init(data[0]), binsha=data[1])
        stream = BytesIO()
        stream.write(data[2])
        stream.seek(0)
        commit._deserialize(stream)
        return commit

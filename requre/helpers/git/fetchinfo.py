# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Any, Callable, List
from io import BytesIO
from git.remote import FetchInfo
from git import Commit
from git.repo.base import Repo
from git.util import IterableList
from git.refs.head import Head
from requre.objects import ObjectStorage
from requre.helpers.files import StoreFiles


class FetchInfoStorageList(ObjectStorage):
    # TODO: improve handling of "ref" item (need deep inspection of git objects and consequences)
    # it is not mandatory for current packit operations
    __ignored = []
    __response_keys_special: List[str] = ["old_commit", "ref"]
    __response_keys = list(
        set(FetchInfo.__slots__) - set(__ignored) - set(__response_keys_special)
    )

    object_type = IterableList
    # failover repo
    repo: Repo

    def to_serializable(self, obj: Any) -> Any:
        output = list()
        for item in obj:
            tmp = dict()
            for key in self.__response_keys:
                tmp[key] = getattr(item, key)

            for key in self.__response_keys_special:
                if key == "old_commit":
                    old_commit = getattr(item, key)
                    if not old_commit:
                        continue
                    stream = BytesIO()
                    old_commit._serialize(stream)
                    stream.flush()
                    value = stream.getvalue()
                    tmp[key] = [old_commit.repo.git_dir, old_commit.binsha, value]
                if key == "ref":
                    ref = getattr(item, key)
                    if ref and isinstance(ref, Head):
                        tmp[key] = ["Head", ref.repo.git_dir, ref.path]
            output.append(tmp)
            # if old_commit:
            #    print([("====", x, getattr(old_commit, x)) for x in old_commit.__slots__])
        return output

    def from_serializable(self, data: Any) -> Any:
        out = self.object_type("name")
        for item in data:
            tmp = FetchInfo(None, None, None, None)
            for key in self.__response_keys:
                setattr(tmp, key, item[key])
            for key in self.__response_keys_special:
                if key == "old_commit" and key in item:
                    old_commit = Commit(repo=self.repo, binsha=item[key][1])
                    stream = BytesIO()
                    stream.write(item[key][2])
                    stream.seek(0)
                    old_commit._deserialize(stream)
                    setattr(tmp, key, old_commit)
                if key == "ref" and key in item:
                    if item[key][0] == "Head":
                        ref = Head(self.repo, item[key][2])
                        setattr(tmp, key, ref)
                        print(" READ >>>>", ref)
            out.append(tmp)
        return out


class RemoteFetch(FetchInfoStorageList):
    """
    Use this class for git.remote.Remote.fetch recording
    """

    stack_internal_check = False

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

        git_object = args[0]
        cls.repo = git_object.repo
        output = super().execute(keys, func, *args, **kwargs)
        git_dir = git_object.repo.git_dir
        StoreFiles.explicit_reference(git_dir)
        if not kwargs["cassette"].do_store(keys):
            # mimic the code in git for read mode for Remote.fetch
            # https://github.com/gitpython-developers/GitPython/blob/master/git/remote.py
            if hasattr(git_object.repo.odb, "update_cache"):
                git_object.repo.odb.update_cache()
        return output

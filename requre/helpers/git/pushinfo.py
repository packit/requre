# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import os
from typing import Any, Callable

from git.refs.head import HEAD
from git.remote import PushInfo
from git.repo.base import Repo
from git.util import IterableList

from requre.objects import ObjectStorage
from requre.helpers.files import StoreFiles


class PushInfoStorageList(ObjectStorage):
    __ignored = ["_remote"]
    __response_keys_special = ["local_ref"]
    __response_keys = list(
        set(PushInfo.__slots__) - set(__ignored) - set(__response_keys_special)
    )
    stack_internal_check = False

    object_type = IterableList

    def to_serializable(self, obj: Any) -> Any:
        output = list()
        for item in obj:
            tmp = dict()
            for key in self.__response_keys:
                tmp[key] = getattr(item, key)
            for key in self.__response_keys_special:
                if key == "local_ref":
                    tmp[key] = [
                        getattr(item, key).repo.git_dir,
                        getattr(item, key).path,
                    ]
            output.append(tmp)
        return output

    def from_serializable(self, data: Any) -> Any:
        out = self.object_type("name")
        for item in data:
            tmp = PushInfo(None, None, None, None)
            for key in self.__response_keys:
                setattr(tmp, key, item[key])
            for key in self.__response_keys_special:
                if key == "local_ref":
                    setattr(tmp, key, HEAD(Repo(item[key][0])))
            out.append(tmp)
        return out

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

        output = super().execute(keys, func, *args, **kwargs)
        git_object = args[0]
        remote_url = git_object.repo.remotes[git_object.name].url
        if os.path.isdir(remote_url):
            StoreFiles.explicit_reference(remote_url)
        return output

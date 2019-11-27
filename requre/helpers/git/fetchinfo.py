# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from typing import Any, Callable, List

from git.remote import FetchInfo
from git.util import IterableList
from requre.storage import PersistentObjectStorage
from requre.objects import ObjectStorage
from requre.helpers.files import StoreFiles


class FetchInfoStorageList(ObjectStorage):
    # TODO: improve handling of "ref" item (need deep inspection of git objects and consequences)
    # it is not mandatory for current packit operations
    __ignored = ["ref"]
    __response_keys_special: List[str] = []
    __response_keys = list(
        set(FetchInfo.__slots__) - set(__ignored) - set(__response_keys_special)
    )

    object_type = IterableList

    def to_serializable(self, obj: Any) -> Any:
        output = list()
        for item in obj:
            tmp = dict()
            for key in self.__response_keys:
                tmp[key] = getattr(item, key)
            output.append(tmp)
        return output

    def from_serializable(self, data: Any) -> Any:
        out = self.object_type("name")
        for item in data:
            tmp = FetchInfo(None, None, None, None)
            for key in self.__response_keys:
                setattr(tmp, key, item[key])
            out.append(tmp)
        return out


class RemoteFetch(FetchInfoStorageList):
    """
    Use this class for git.remote.Remote.fetch recording
    """

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
        git_dir = git_object.repo.git_dir
        StoreFiles.explicit_reference(git_dir)
        if not PersistentObjectStorage().do_store(keys):
            # mimic the code in git for read mode for Remote.fetch
            # https://github.com/gitpython-developers/GitPython/blob/master/git/remote.py
            if hasattr(git_object.repo.odb, "update_cache"):
                git_object.repo.odb.update_cache()
        return output

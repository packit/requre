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

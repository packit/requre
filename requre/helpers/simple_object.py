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

from typing import Any, Optional, Dict
from requre.objects import ObjectStorage


class Simple(ObjectStorage):
    """
    Use this object, when your output is directly YAML serializable, basic objects e.g.
       string, number, boolean, list, dict of these basic objects
    """

    def from_serializable(self, data: Any) -> Any:
        return data

    def to_serializable(self, obj: Any) -> Any:
        return obj


class Void(Simple):
    """
    Use this object, when don't want to store output data of function.
    Could be used for debugging purposes, to see caller arguments
    or output is not important or unable to serialize anyhow.
    """

    def write(self, obj: Any, metadata: Optional[Dict] = None) -> Any:
        """
        Write the object representation to storage
        Internally it will use self.to_serializable()
        method to get serializable object representation

        :param obj: some object
        :param metadata: store metedata to object
        :return: same obj
        """
        self.get_cassette().store(
            self.store_keys,
            f">>>>> Requre output supressed by using {self.__class__.__name__}",
            metadata=metadata,
        )
        return obj


class Tuple(Simple):
    def to_serializable(self, obj):
        return list(obj)

    def from_serializable(self, data):
        return tuple(data)

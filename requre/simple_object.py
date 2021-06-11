# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Optional

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

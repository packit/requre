# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import yaml
import logging
import pickle
import warnings

from typing import Any, Dict, Optional
from requre.objects import ObjectStorage
from requre.helpers.simple_object import Simple, Void, Tuple

logger = logging.getLogger(__name__)
GUESS_STR = "guess_type"


class Guess(Simple):
    """
    This class is able to store/read all simple types in requre
    Void, Simple, ObjectStorage (pickle)
    It select proper type if possible.

    Warning: when it uses ObjectStorage, it may lead some secrets to pickled objects
    and it could be hidden inside object representation.
    """

    @staticmethod
    def guess_type(value):
        if isinstance(value, tuple):
            return Tuple
        try:
            # Try to use type for storing simple output (list, dict, str, nums, etc...)
            yaml.safe_dump(value)
            return Simple
        except Exception:
            try:
                # Try to store anything serializable via pickle module
                pickle.dumps(value)
                return ObjectStorage
            except Exception:
                # do not store anything if not possible directly
                warnings.warn(
                    "Guess class - nonserializable return object - "
                    f"Using supressed output, are you sure? {value}"
                )
                return Void

    def write(self, obj: Any, metadata: Optional[Dict] = None) -> Any:
        """
        Write the object representation to storage
        Internally it will use self.to_serializable
        method to get serializable object representation

        :param obj: some object
        :param metadata: store metedata to object
        :return: same obj
        """
        object_serialization_type = self.guess_type(obj)
        metadata[GUESS_STR] = object_serialization_type.__name__
        instance = object_serialization_type(
            store_keys=self.store_keys,
            cassette=self.get_cassette(),
            storage_object_kwargs=self.storage_object_kwargs,
        )
        return instance.write(obj, metadata=metadata)

    def read(self):
        """
        Crete object representation of serialized data in persistent storage
        Internally it will use self.from_serializable method transform object

        :return: proper object
        """
        data = self.get_cassette()[self.store_keys]
        guess_type = self.get_cassette().data_miner.metadata[GUESS_STR]
        if guess_type == ObjectStorage.__name__:
            return pickle.loads(data)
        elif guess_type == Simple.__name__:
            return data
        elif guess_type == Void.__name__:
            return data
        elif guess_type == Tuple.__name__:
            return tuple(data)
        else:
            raise ValueError(
                f"Unsupported type of stored object inside cassette: {guess_type}"
            )

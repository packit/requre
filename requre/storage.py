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

import os
import time
from _collections_abc import Hashable
from typing import Dict, List, Any, Optional

from enum import Enum
import yaml

from .exceptions import PersistentStorageException
from .singleton import SingletonMeta
from .constants import VERSION_REQURE_FILE, ENV_STORAGE_FILE

# use this sleep to avoid decorating original time function used internally
original_sleep = time.sleep
original_time = time.time


class DataStructure:
    """
    Object model for storing data to persistent storage
    """

    OUTPUT_KEY = "output"
    METADATA_KEY = "metadata"

    def __init__(self, output: Any):
        self.output = output
        self._metadata: dict = dict()

    @property
    def metadata(self):
        """
        Medatata for item in storage
        """
        return self._metadata

    @metadata.setter
    def metadata(self, values: dict):
        for k, v in values.items():
            self._metadata[k] = v

    def dump(self):
        """
        Dump object to serializable format

        :return dict
        """
        return {self.METADATA_KEY: self.metadata, self.OUTPUT_KEY: self.output}

    @classmethod
    def create_from_dict(cls, dict_repr: dict):
        """
        Create Object representation from dict

        :return DataStructure
        """
        data = cls(dict_repr[cls.OUTPUT_KEY])
        data.metadata = dict_repr[cls.METADATA_KEY]
        return data


class DataTypes(Enum):
    List = 1
    Dict = 2


class DataMiner(metaclass=SingletonMeta):
    """
    Intermediate class used for proper formatting and keeping backward
    compatibility with requre storage version files
    """

    current_time = original_time()
    data: DataStructure
    data_type: DataTypes = DataTypes.List
    use_latency = False
    LATENCY_KEY = "latency"

    def get_latency(self, regenerate=True) -> float:
        """
        Returns latency from last store event

        :param regenerate: if False, then it will not be changed, just displayed
        :return: float
        """
        current_time = original_time()
        diff = current_time - self.current_time
        if regenerate:
            self.current_time = current_time
        return diff

    def dump(self, level, key, values, metadata: Optional[Dict] = None):
        """
        Store values in proper format to level[key] item

        :param level: parent dict object
        :param key: item in dict
        :param values: what to strore (return value of function)
        :param metadata: store metadata to object from upper level
        :return: None
        """
        ds = DataStructure(values)
        if metadata:
            ds.metadata = metadata
        if self.LATENCY_KEY not in ds.metadata:
            ds.metadata = {self.LATENCY_KEY: self.get_latency()}
        self.data = ds
        item = ds.dump()
        if self.data_type == DataTypes.List:
            if PersistentObjectStorage().storage_file_version <= 1:
                # Backward compatibility for requre before using DataStructure
                item = values
            level.setdefault(key, [])
            level[key].append(item)
        elif self.data_type == DataTypes.Dict:
            level[key] = item

    def load(self, level):
        """
        Get data from storage_object and trasform it to DataStructure object.

        :param level: where data are stored
        :return: output of function
        """
        data = None
        if self.data_type == DataTypes.List:
            if len(level) == 0:
                raise PersistentStorageException(
                    "No responses left. Try to regenerate response file "
                    f"({PersistentObjectStorage().storage_file})."
                )
            if PersistentObjectStorage().storage_file_version <= 1:
                # Backward compatibility for requre before using DataStructure
                data = DataStructure(level[0])
            else:
                data = DataStructure.create_from_dict(level[0])
            del level[0]
        elif self.data_type == DataTypes.Dict:
            data = DataStructure.create_from_dict(level)
        self.data = data
        if self.use_latency:
            original_sleep(data.metadata.get(self.LATENCY_KEY, 0))
        return data.output

    @property
    def metadata(self):
        return self.data.metadata

    @metadata.setter
    def metadata(self, value):
        self.data.metadata = value


class PersistentObjectStorage(metaclass=SingletonMeta):
    """
    Class implements reading/writing simple JSON requests to dict structure
    and return values based on keys.
    It contains methods to reads/stores data to object and load and store them to YAML file

    storage_object: dict with structured data based on keys (eg. simple JSON requests)
    storage_file: file for reading and writing data in storage_object
    """

    internal_object_key = "_requre"
    version_key = "version_storage_file"

    def __init__(self) -> None:
        # call dump() after store() is called
        self.dump_after_store = False
        self._is_write_mode: bool = False
        self.is_flushed = True
        self.storage_object: dict = {}
        self._storage_file: Optional[str] = None
        storage_file_from_env = os.getenv(ENV_STORAGE_FILE)
        if storage_file_from_env:
            self.storage_file = storage_file_from_env

    @property
    def metadata(self):
        """
        Placeholder to store some custom configuration, or store custom data,
        eg. version of storage file, or some versions of packages

        :return: dict
        """
        return self.storage_object.get(self.internal_object_key, {})

    @metadata.setter
    def metadata(self, key_dict: dict):
        if self.internal_object_key not in self.storage_object:
            self.storage_object[self.internal_object_key] = {}
        for k, v in key_dict.items():
            self.storage_object[self.internal_object_key][k] = v
        self.is_flushed = False

    @property
    def storage_file_version(self):
        """
        Get version of persistent storage file
        :return: int
        """
        return self.metadata.get(self.version_key, 0)

    @storage_file_version.setter
    def storage_file_version(self, value: int):
        self.metadata = {self.version_key: value}

    def _set_storage_file_version_if_not_set(self):
        """
        Set storage file version if not already set to latest version.
        """
        if self.metadata.get(self.version_key) is None:
            self.storage_file_version = VERSION_REQURE_FILE

    @property
    def storage_file(self):
        return self._storage_file

    @storage_file.setter
    def storage_file(self, value):
        self._storage_file = value
        self._is_write_mode = not os.path.exists(self._storage_file)
        if self.is_write_mode:
            self.is_flushed = False
            self.storage_object = {}
        else:
            self.storage_object = self.load()

    @property
    def is_write_mode(self):
        return self._is_write_mode

    @staticmethod
    def transform_hashable(keys: List) -> List:
        output: List = []
        for item in keys:
            if not item:
                output.append("empty")
            elif not isinstance(item, Hashable):
                output.append(str(item))
            else:
                output.append(item)
        return output

    def store(self, keys: List, values: Any, metadata: Optional[Dict] = None) -> None:
        """
        Stores data to dictionary object based on keys values it will create structure
        if structure does not exist

        It implicitly changes type to string if key is not hashable

        :param keys: items what will be used as keys for dictionary
        :param values: It could be whatever type what is used in original object handling
        :return: None
        """
        self._set_storage_file_version_if_not_set()
        current_level = self.storage_object
        hashable_keys = self.transform_hashable(keys)
        for item_num in range(len(hashable_keys)):
            item = hashable_keys[item_num]
            if item_num + 1 < len(hashable_keys):
                if not current_level.get(item):
                    current_level[item] = {}
            else:
                DataMiner().dump(
                    level=current_level, key=item, values=values, metadata=metadata
                )
            current_level = current_level[item]
        self.is_flushed = False

        if self.dump_after_store:
            self.dump()

    def read(self, keys: List) -> Any:
        """
        Reads data from dictionary object structure based on keys.
        If keys does not exists

        It implicitly changes type to string if key is not hashable

        :param keys: key list for searching in dict
        :return: value assigged to key items
        """
        current_level = self.storage_object
        hashable_keys = self.transform_hashable(keys)
        for item in hashable_keys:

            if item not in current_level:
                raise PersistentStorageException(
                    f"Keys not in storage:{self.storage_file} {hashable_keys}"
                )

            current_level = current_level[item]
        result = DataMiner().load(level=current_level)
        return result

    def dump(self) -> None:
        """
        Explicitly stores content of storage_object to storage_file path

        This method is also called when object is deleted and is set write mode to True

        :return: None
        """
        if self.is_write_mode:
            self._set_storage_file_version_if_not_set()
            if self.is_flushed:
                return None
            with open(self.storage_file, "w") as yaml_file:
                yaml.dump(self.storage_object, yaml_file, default_flow_style=False)
            self.is_flushed = True

    def load(self) -> Dict:
        """
        Explicitly loads file content of storage_file to storage_object and return as well

        :return: dict
        """
        with open(self.storage_file, "r") as yaml_file:
            output = yaml.safe_load(yaml_file)
        self.storage_object = output
        return output


def use_persistent_storage_without_overwriting(cls):
    class ClassWithPersistentStorage(cls):
        persistent_storage: Optional[
            PersistentObjectStorage
        ] = PersistentObjectStorage()

    ClassWithPersistentStorage.__name__ = cls.__name__
    return ClassWithPersistentStorage


class StorageCounter:
    counter = 0
    dir_suffix = "file_storage"
    previous = None

    @classmethod
    def reset_counter_if_changed(cls):
        current = os.path.basename(PersistentObjectStorage().storage_file)
        if cls.previous != current:
            cls.counter = 0
            cls.previous = current

    @classmethod
    def next(cls):
        cls.counter += 1
        return cls.counter

    @staticmethod
    def storage_file():
        return os.path.basename(PersistentObjectStorage().storage_file)

    @staticmethod
    def storage_dir():
        return os.path.dirname(PersistentObjectStorage().storage_file)

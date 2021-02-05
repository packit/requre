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

import inspect
import logging
import os
import sys
import time
from enum import Enum
from typing import Dict, Optional, List, Hashable, Any, Callable

import yaml

from requre.constants import (
    METATADA_KEY,
    ENV_REQURE_STORAGE_MODE,
    ENV_STORAGE_FILE,
    VERSION_REQURE_FILE,
    KEY_MINIMAL_MATCH,
)
from requre.exceptions import (
    PersistentStorageException,
    ItemNotInStorage,
    StorageNoResponseLeft,
)
from requre.utils import StorageMode

# use this sleep to avoid decorating original time function used internally
original_sleep = time.sleep
original_time = time.time
logger = logging.getLogger(__name__)


class CassetteExecution:
    """
    Execution wrapper for cassette decorators
    """

    def __init__(self):
        self._function = None
        self._cassette = None
        self._obj_cls = None

    @property
    def function(self):
        """
        return stored function
        """
        return self._function

    @function.setter
    def function(self, value):
        self._function = value

    @property
    def cassette(self):
        """
        return current cassette for function execution
        """
        return self._cassette

    @cassette.setter
    def cassette(self, value):
        self._cassette = value

    def __call__(self, *args, **kwargs):
        """
        backward compatibility and for usage within inport system.
        please use this carrefully, in case of object instance it removes self
        """
        # TODO: fix issue with self removing
        return self.function(*args, **kwargs)

    @property
    def obj_cls(self):
        return self._obj_cls

    @obj_cls.setter
    def obj_cls(self, value):
        self._obj_cls = value


class StorageKeysInspect:
    @staticmethod
    def get_base_keys(func: Callable) -> List[Any]:
        raise NotImplementedError("Use child classes")


class StorageKeysInspectFull(StorageKeysInspect):
    @staticmethod
    def get_base_keys(func: Callable) -> List[Any]:
        output: List[str] = list()
        # callers module list, to be able to separate requests for various services in one file
        caller_list: List[str] = list()
        for currnetframe in inspect.stack():
            if not inspect.getmodule(currnetframe[0]):
                continue
            module_name = inspect.getmodule(currnetframe[0]).__name__
            if module_name.startswith("_"):
                break
            # avoid to store requre.storage to module stack
            # backward compatibility issue
            if module_name.startswith("requre.storage"):
                continue
            if len(caller_list) and caller_list[-1] == module_name:
                continue
            else:
                caller_list.append(module_name)
        output += caller_list[::-1]
        # module name where function is
        output.append(inspect.getmodule(func).__name__)
        # name of function what were used
        output.append(func.__name__)
        return output


class StorageKeysInspectOuter(StorageKeysInspect):
    @staticmethod
    def get_base_keys(func: Callable) -> List[Any]:
        """
        return shorter stack information what will end after info goes to CWD.
        Be careful: You have to use same scheduler (when you regenerate tests via pytest and
        then run them via tox, it causes that tox what uses python venv installs all deps to
        .tox subdir, so that .tox files will be in CWD then)
        example: full stack info for packit project:

        "long python execute handling":
          unittest.case:
            tests_recording.test_status:
              packit.status:
                ogr.services.pagure.project:
                  ogr.services.pagure.service:
                    requests.sessions:
                      requre.objects:
                        requests.sessions:
                            send:
        the current one remove all stack info before it goes to current directory (including)
                ogr.services.pagure.project:
                  ogr.services.pagure.service:
                    requests.sessions:
                      requre.objects:
                        requests.sessions:
                            send:

        """
        output: List[str] = list()
        # callers module list, to be able to separate requests for various services in one file
        caller_list: List[str] = list()
        for currnetframe in inspect.stack():
            module_info = inspect.getmodule(currnetframe[0])
            # sometimes module_info is empty and not possible to found any info.
            if not module_info:
                continue
            module_name = module_info.__name__
            module_file = module_info.__file__
            # If python stack is already in directory you are (CWD) then stop appending
            # Because you dont want to track changes of test call stack or your project stack
            # This is main feature regarding to StorageKeysInspectFull, what stores it as well
            # and may cause issue with unittest execution changes
            if os.path.realpath(os.getcwd()) in os.path.realpath(module_file):
                break
            # avoid to store requre.storage to module stack
            # backward compatibility issue
            if module_name.startswith("requre.storage"):
                continue
            # avoid duplication in stack information, e.g. one method will can another one from
            # same file/module, so avoid to add it to list, in case already here on last position.
            if len(caller_list) and caller_list[-1] == module_name:
                continue
            else:
                caller_list.append(module_name)
        output += caller_list[::-1]
        # module name where function is
        output.append(inspect.getmodule(func).__name__)
        # name of function what were used
        output.append(func.__name__)
        return output


class StorageKeysInspectSimple(StorageKeysInspect):
    @staticmethod
    def get_base_keys(func: Callable) -> List[Any]:
        return [inspect.getmodule(func).__name__, func.__name__]


class StorageKeysInspectUnique(StorageKeysInspect):
    @staticmethod
    def get_base_keys(func: Callable) -> List[Any]:
        return StorageKeysInspectUnique._get_unique_keys(
            StorageKeysInspectFull.get_base_keys(func)
        )

    @staticmethod
    def _get_unique_keys(keys):
        output: List = []
        for item in reversed(keys):
            if item not in output:
                output.append(item)
        return list(reversed(output))


StorageKeysInspectDefault = StorageKeysInspectFull


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
    def create_from_value(cls, dict_repr: dict):
        """
        Create Object representation from dict

        :return DataStructure
        """
        data = cls(dict_repr[cls.OUTPUT_KEY])
        data.metadata = dict_repr[cls.METADATA_KEY]
        return data

    @classmethod
    def create_from_dict(cls, dict_repr: dict, cassette: Any):
        """
        Create Object representation from dict

        :param cassette: Cassette instance to pass inside object to work with
        :return DataStructure
        """
        if cassette.data_miner.key not in dict_repr:
            raise ItemNotInStorage(
                f"Key '{cassette.data_miner.key}' not in the response file. "
                f"(Be sure that you generate the response file "
                f"for this variant.)"
            )
        value = dict_repr[cassette.data_miner.key]
        data = cls(value[cls.OUTPUT_KEY])
        data.metadata = value[cls.METADATA_KEY]
        return data

    @classmethod
    def create_from_dict_with_list(cls, dict_repr: dict, cassette: Any):
        """
        Create Object representation from dict with list

        :param cassette: Cassette instance to pass inside object to work with
        :return DataStructure
        """
        if cassette.data_miner.key not in dict_repr:
            raise ItemNotInStorage(
                f"Key '{cassette.data_miner.key}' not in the response file. "
                f"(Be sure that you generate the response file "
                f"for this variant.)"
            )
        value = dict_repr[cassette.data_miner.key]
        return cls.create_from_list(list_repr=value, cassette=cassette)

    @staticmethod
    def create_from_list(list_repr: list, cassette: Any):
        if len(list_repr) == 0:
            raise StorageNoResponseLeft(
                "No responses left. Try to regenerate response file "
                f"({cassette.storage_file})."
            )
        if cassette.storage_file_version <= 1:
            # Backward compatibility for requre before using DataStructure
            data = DataStructure(list_repr[0])
        else:
            data = DataStructure.create_from_value(list_repr[0])
        del list_repr[0]
        return data


class DataTypes(Enum):
    List = 1
    Value = 2
    Dict = 3
    DictWithList = 4


class DataMiner:
    """
    Intermediate class used for proper formatting and keeping backward
    compatibility with requre storage version files
    """

    def __init__(self):
        self.current_time = original_time()
        self.data: Optional[DataStructure] = None
        self.data_type: DataTypes = DataTypes.List
        self.use_latency = False
        self.LATENCY_KEY = "latency"
        self.key: str = "all"
        self.key_stategy_cls = StorageKeysInspectDefault
        self.store_arg_debug_metadata = False
        self.METADATA_ARG_DEBUG_KEY = "log_call_function"
        self.METADATA_CALLER_LIST = "module_call_list"
        self.read_key_exact = False

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

    def dump(self, level, key, values, metadata: Dict, cassette: Any):
        """
        Store values in proper format to level[key] item

        :param level: parent dict object
        :param key: item in dict
        :param values: what to store (return value of function)
        :param metadata: store metadata to object from upper level
        :param cassette: Cassette instance to pass inside object to work with
        :return: None
        """
        ds = DataStructure(values)
        if metadata:
            ds.metadata = metadata
        if self.LATENCY_KEY not in ds.metadata:
            ds.metadata = {self.LATENCY_KEY: self.get_latency()}
        self.data = ds
        item = ds.dump()
        if self.data_type == DataTypes.Dict:
            level.setdefault(key, {})
            level[key][self.key] = item
        elif self.data_type == DataTypes.DictWithList:
            level.setdefault(key, {})
            level[key].setdefault(self.key, [])
            level[key][self.key].append(item)
        elif self.data_type in [DataTypes.List, DataTypes.DictWithList]:
            if cassette.storage_file_version <= 1:
                # Backward compatibility for requre before using DataStructure
                item = values
            level.setdefault(key, [])
            level[key].append(item)
        elif self.data_type == DataTypes.Dict:
            level.setdefault(key, {})
            level[key][self.key] = item
        else:
            level[key] = item

    def load(self, level, cassette: Any):
        """
        Get data from storage_object and trasform it to DataStructure object.

        :param level: where data are stored
        :param cassette: Cassette instance to pass inside object to work with
        :return: output of function
        """
        data = None
        if self.data_type == DataTypes.List:
            data = DataStructure.create_from_list(level, cassette=cassette)
        elif self.data_type == DataTypes.Value:
            data = DataStructure.create_from_value(level)
        elif self.data_type == DataTypes.Dict:
            data = DataStructure.create_from_dict(level, cassette=cassette)
        elif self.data_type == DataTypes.DictWithList:
            data = DataStructure.create_from_dict_with_list(level, cassette=cassette)
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


class Cassette:
    """
    Class implements reading/writing simple JSON requests to dict structure
    and return values based on keys.
    It contains methods to reads/stores data to object and load and store them to YAML file

    storage_object: dict with structured data based on keys (eg. simple JSON requests)
    storage_file: file for reading and writing data in storage_object
    """

    @property
    def content(self) -> dict:
        return self.storage_object

    internal_object_key = METATADA_KEY
    version_key = "version_storage_file"
    key_inspect_strategy_key = "key_strategy"

    def _set_defaults(self) -> None:
        self.dump_after_store = False
        self.is_flushed = False
        self.storage_object: dict = {}
        self._storage_file: Optional[str] = None
        self.data_miner = DataMiner()
        self.mode = StorageMode.default

    def __init__(self) -> None:
        # call dump() after store() is called
        self._set_defaults()
        storage_file_from_env = os.getenv(ENV_STORAGE_FILE)
        if storage_file_from_env:
            self.storage_file = storage_file_from_env

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"storage_mode={self.mode}, "
            f"storage_file={self._storage_file})"
        )

    def __repr__(self) -> str:
        return self.__str__()

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

    def do_store(self, keys):
        if self.mode == StorageMode.read and not os.path.exists(self.storage_file):
            raise PersistentStorageException(
                "Requre can't work in this setup: we are meant to read "
                "recorded responses but the storage file does not exist."
            )
        if self.mode == StorageMode.read:
            return False

        elif self.mode == StorageMode.write:
            return True

        elif self.mode == StorageMode.append:
            if self.data_miner.data_type in [DataTypes.DictWithList, DataTypes.List]:
                # append possible
                return True

            if (
                self.data_miner.data_type in [DataTypes.Dict, DataTypes.Value]
                and keys not in self
            ):
                # keys present => we can read the values
                return True
            return False

        key_present = keys in self
        logger.warning(
            f"No storage-mode set. Checking presence of the keys: {key_present} "
            f"=> {'read' if key_present else 'store'}"
        )
        return not key_present

    @storage_file_version.setter  # type: ignore
    def storage_file_version(self, value: int):
        self.metadata = {self.version_key: value}

    def _set_storage_metadata_if_not_set(self):
        """
        Set storage file version if not already set to latest version.
        """
        if self.metadata.get(self.version_key) is None:
            self.storage_file_version = VERSION_REQURE_FILE
        if self.metadata.get(self.key_inspect_strategy_key) is None:
            self.metadata = {
                self.key_inspect_strategy_key: self.data_miner.key_stategy_cls.__name__
            }
        data_type_name = DataTypes.__name__
        if self.metadata.get(data_type_name) is None:
            self.metadata = {data_type_name: self.data_miner.data_type.value}

    def _set_storage_mode(self, storage_file):
        # use env var mode if given as the most important
        storage_mode = os.getenv(ENV_REQURE_STORAGE_MODE)
        if storage_mode:
            logger.info(
                f"You overrided storage mode via env var {ENV_REQURE_STORAGE_MODE}={storage_mode}"
            )
            if not hasattr(StorageMode, storage_mode):
                raise PersistentStorageException(
                    f"storage mode '{storage_mode}' does not exist, "
                    f"use one of {list(StorageMode.__members__.keys())}) "
                )
            self.mode: StorageMode = getattr(StorageMode, storage_mode)

        # if not given by ENV VAR, guess mode via file existence
        else:
            if not os.path.exists(storage_file):
                if self.mode == StorageMode.default:
                    self.mode = StorageMode.write
            else:
                if self.mode == StorageMode.default:
                    self.mode = StorageMode.read
                self.storage_object = self.load()
        if self.mode == StorageMode.read and not os.path.exists(storage_file):
            raise PersistentStorageException(
                "Requre can't work in this setup: we are meant to read"
                f" recorded responses but the storage file ({storage_file}) "
                "does not exist."
            )

    @property
    def storage_file(self):
        return self._storage_file

    @storage_file.setter
    def storage_file(self, value):
        # when set to None, reset to default
        logger.info(f"SETTING SF: {value} for cassette {id(self)} - {self}")
        if value is None:
            self._set_defaults()
            return
        # when file is changed set PersistenStorage default values
        if self._storage_file != value:
            self._set_defaults()
            self._storage_file = value
        self._set_storage_mode(storage_file=self._storage_file)
        # load data for read.
        if self.mode == StorageMode.read:
            self.storage_object = self.load()
        # if append mode load data just in case file exists.
        if self.mode == StorageMode.append and os.path.exists(self._storage_file):
            self.storage_object = self.load()

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

    def _pretty_dict_output(self, input_dict: Optional[dict] = None, depth=0, sep="  "):
        if not isinstance(input_dict, dict):
            return
        for key, value in input_dict.items():
            yield (sep * depth) + str(key)
            yield from self._pretty_dict_output(value, depth + 1)

    def _printable_dict_output(self, input_dict: dict):
        return (
            "Current internal object structure:"
            + "\n"
            + "\n".join(list(self._pretty_dict_output(self.storage_object)))
        )

    def store(self, keys: List, values: Any, metadata: Dict) -> None:
        """
        Stores data to dictionary object based on keys values it will create structure
        if structure does not exist

        It implicitly changes type to string if key is not hashable

        :param keys: items what will be used as keys for dictionary
        :param values: It could be whatever type what is used in original object handling
        :return: None
        """
        self._set_storage_metadata_if_not_set()
        current_level = self.storage_object
        level_trace = []
        hashable_keys = self.transform_hashable(keys)
        for item_num in range(len(hashable_keys)):
            item = hashable_keys[item_num]
            level_trace.append(item)
            if item_num + 1 < len(hashable_keys):
                if not isinstance(current_level, dict):
                    print(
                        self._printable_dict_output(self.storage_object),
                        file=sys.stderr,
                    )
                    raise PersistentStorageException(
                        "you are mixing various depths of stored data: keys:"
                        f" {hashable_keys}, current levels: {level_trace}"
                    )
                if not current_level.get(item):
                    current_level[item] = {}
            else:
                self.data_miner.dump(
                    level=current_level,
                    key=item,
                    values=values,
                    metadata=metadata,
                    cassette=self,
                )
            current_level = current_level[item]
        self.is_flushed = False

        if self.dump_after_store:
            self.dump()
        logger.debug(f"Storing response to: {self.storage_file}: {hashable_keys}")

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
        debug_keys: List[str] = []
        matched_calls: List[str] = []
        list_len = len(hashable_keys)
        for item_num in range(list_len):
            item = hashable_keys[item_num]
            if item not in current_level:
                # it matched last 2 items
                if self.data_miner.read_key_exact or (
                    not self.data_miner.read_key_exact
                    and item_num + KEY_MINIMAL_MATCH >= list_len
                ):
                    # if not matched, but consider if it is not same key as previous
                    # it is important if simplify used.
                    if matched_calls and item == matched_calls[-1]:
                        debug_keys.append(f"DUPLICATE {item}")
                        continue
                    print(
                        self._printable_dict_output(self.storage_object),
                        file=sys.stderr,
                    )
                    raise ItemNotInStorage(
                        f"Keys not in storage:{self.storage_file}"
                        f" Matched: {debug_keys},"
                        f" Missing: {hashable_keys[item_num:]}"
                    )
                else:
                    debug_keys.append(f"SKIP {item}")

            else:
                debug_keys.append(item)
                matched_calls.append(item)
                current_level = current_level[item]
        try:
            result = self.data_miner.load(level=current_level, cassette=self)
        except StorageNoResponseLeft as e:
            raise StorageNoResponseLeft(f"{e.args} (keys: {debug_keys})")
        logger.debug(f"Reading response from: {self.storage_file}: {debug_keys}")
        return result

    def __contains__(self, item) -> bool:
        current_level = self.storage_object
        hashable_keys = self.transform_hashable(item)
        for item in hashable_keys:
            if item not in current_level:
                return False
            current_level = current_level[item]
        if self.data_miner.data_type in [DataTypes.Dict, DataTypes.DictWithList]:
            return self.data_miner.key in current_level
        return True

    def __getitem__(self, key):
        return self.read(keys=key)

    def __setitem__(self, key, value):
        self.store(keys=key, values=value, metadata={})

    def __delitem__(self, key):
        current_level = self.storage_object
        hashable_keys = self.transform_hashable(key)
        last_level = None
        for item in hashable_keys:
            if item not in current_level:
                raise ItemNotInStorage(
                    f"Key not found in the persistent storage: {key}"
                )
            last_level = current_level
            current_level = current_level[item]

        if self.data_miner.data_type == DataTypes.Dict:
            del current_level[self.data_miner.key]
        else:
            del last_level[key[-1]]

    def dump(self) -> None:
        """
        Explicitly stores content of storage_object to storage_file path

        This method is also called when object is deleted and is set write mode to True

        :return: None
        """
        if self.mode in [StorageMode.write, StorageMode.append]:
            self._set_storage_metadata_if_not_set()
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
        # set proper storage strategy if stored in file
        if self.metadata.get(self.key_inspect_strategy_key):
            logger.debug(
                f"Used key strategy: {self.metadata.get(self.key_inspect_strategy_key)}"
            )
            self.data_miner.key_stategy_cls = globals()[
                self.metadata.get(self.key_inspect_strategy_key)
            ]
        return output

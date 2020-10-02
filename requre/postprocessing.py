import os
import logging
from typing import Union, Any, Dict, Optional, List
from .constants import KEY_MINIMAL_MATCH, METATADA_KEY
from .cassette import DataMiner, DataStructure, DataTypes
from glob import glob
import tarfile
import tempfile
import shutil
from subprocess import check_output, CalledProcessError
import hashlib
from _hashlib import HASH as Hash
from pathlib import Path

logger = logging.getLogger(__name__)


class DictProcessing:
    def __init__(self, requre_dict: dict):
        self.requre_dict = requre_dict

    def match(self, selector: list, internal_object: Union[dict, list, None] = None):
        if internal_object is None:
            internal_object = self.requre_dict
        if len(selector) == 0:
            logger.debug("all selectors matched")
            yield internal_object
            # add return here, to avoid multiple returns
            return
        if isinstance(internal_object, dict):
            for k, v in internal_object.items():
                if v is None:
                    return
                if selector and selector[0] == k:
                    logger.debug(f"selector {k} matched")
                    yield from self.match(selector=selector[1:], internal_object=v)
                else:
                    yield from self.match(selector=selector, internal_object=v)
        elif isinstance(internal_object, list):
            for list_item in internal_object:
                if list_item is None:
                    return
                yield from self.match(selector=selector, internal_object=list_item)
        else:
            return

    @staticmethod
    def replace(obj: Any, key: Any, value: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    logger.debug(f"replacing: {obj[key]} by {value}")
                    obj[key] = value
                else:
                    DictProcessing.replace(obj=v, key=key, value=value)
        if isinstance(obj, list):
            for item in obj:
                DictProcessing.replace(obj=item, key=key, value=value)

    @staticmethod
    def minimal_match(dict_obj: Dict, metadata: Dict):

        tmp_dict = dict_obj
        first_item: Dict = {}
        key_name = DataTypes.__name__
        ds = DataTypes.List
        if key_name in metadata:
            ds = DataTypes(metadata.get(key_name))
        logger.debug(f"Use datatype: {ds}")
        for cntr in range(KEY_MINIMAL_MATCH):
            if not isinstance(tmp_dict, dict) or len(tmp_dict.keys()) != 1:
                return False
            key = list(tmp_dict.keys())[0]
            value = tmp_dict[key]
            tmp_dict = value
        if ds == DataTypes.DictWithList:
            if isinstance(tmp_dict, dict):
                tmp_first_item = tmp_dict[list(tmp_dict.keys())[0]]
                if isinstance(tmp_first_item, list):
                    first_item = tmp_first_item[0]
        if ds == DataTypes.Dict:
            if isinstance(tmp_dict, dict):
                first_item = tmp_dict[list(tmp_dict.keys())[0]]
        if ds == DataTypes.List:
            if isinstance(tmp_dict, list):
                first_item = tmp_dict[0]
        if ds == DataTypes.Value:
            if isinstance(tmp_dict, dict):
                first_item = tmp_dict
        if isinstance(first_item, dict) and DataMiner().LATENCY_KEY in first_item.get(
            DataStructure.METADATA_KEY, {}
        ):
            logger.debug(
                f"Minimal key path ({KEY_MINIMAL_MATCH}) matched for {first_item.keys()}"
            )
            return True
        return False

    def simplify(
        self, internal_object: Optional[Dict] = None, ignore_list: Optional[List] = None
    ):
        ignore_list = ignore_list or []
        internal_object = (
            self.requre_dict if internal_object is None else internal_object
        )
        if isinstance(internal_object, dict):
            if len(internal_object.keys()) == 1:
                key = list(internal_object.keys())[0]
                if key in [METATADA_KEY] + ignore_list:
                    return
                if self.minimal_match(internal_object, self.requre_dict[METATADA_KEY]):
                    return
                if isinstance(internal_object[key], dict):
                    value = internal_object.pop(key)
                    print(f"Removing key: {key}  -> {list(value.keys())}")
                    for k, v in value.items():
                        internal_object[k] = v
                        self.simplify(
                            internal_object=internal_object, ignore_list=ignore_list
                        )
            else:
                for v in internal_object.values():
                    self.simplify(internal_object=v, ignore_list=ignore_list)


class TarFilesSimilarity:
    def __init__(self, path, hash_function=None):
        self._mapping_table = None
        self.path = path
        self.hash_function = hash_function

    @property
    def mapping_table(self):
        if self._mapping_table is None:
            self._mapping_table = dict()
            for tar_file in self.list_files(self.path):
                current_hash = self.untar_and_return_hash(tar_file, self.hash_function)
                self._mapping_table[tar_file] = current_hash
        return self._mapping_table

    @staticmethod
    def md5_update_from_file(filename: Union[str, Path], hash: Hash) -> Hash:
        # https://stackoverflow.com/questions/24937495/how-can-i-calculate-a-hash-for-a-filesystem-directory-using-python
        assert Path(filename).is_file()
        with open(str(filename), "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash.update(chunk)
        return hash

    @staticmethod
    def md5_file(filename: Union[str, Path]) -> str:
        return str(
            TarFilesSimilarity.md5_update_from_file(filename, hashlib.md5()).hexdigest()
        )

    @staticmethod
    def md5_update_from_dir(directory: Union[str, Path], hash: Hash) -> Hash:
        assert Path(directory).is_dir()
        for path in sorted(Path(directory).iterdir(), key=lambda p: str(p).lower()):
            hash.update(path.name.encode())
            if path.is_file():
                hash = TarFilesSimilarity.md5_update_from_file(path, hash)
            elif path.is_dir():
                hash = TarFilesSimilarity.md5_update_from_dir(path, hash)
        return hash

    @staticmethod
    def md5_dir(directory: Union[str, Path]) -> str:
        return str(
            TarFilesSimilarity.md5_update_from_dir(directory, hashlib.md5()).hexdigest()
        )

    @staticmethod
    def list_files(path, pattern="*.tar.xz"):
        return glob(f"{path}/**/{pattern}", recursive=True)

    @staticmethod
    def hash_fn(content):
        if os.path.isdir(content):
            try:
                os.chdir(content)
                return "git-sha", check_output(["git", "rev-parse", "HEAD"])
            except (FileNotFoundError, CalledProcessError):
                return "md5-dir", TarFilesSimilarity.md5_dir(content)
        else:
            return "md5-file", TarFilesSimilarity.md5_file(content)

    @staticmethod
    def untar_and_return_hash(tar_archive_path, hash_funciton):
        hash_funciton = hash_funciton or TarFilesSimilarity.hash_fn
        tempdir = tempfile.mkdtemp()
        currentdir = os.getcwd()
        try:
            os.chdir(tempdir)
            tar_file = tarfile.open(tar_archive_path)
            tar_file.extractall()
            files = os.listdir(".")
            if len(files) != 1:
                logger.debug("tar not packed by requre")
                return None
            content = files[0]
            return hash_funciton(content)
        finally:
            os.chdir(currentdir)
            shutil.rmtree(tempdir, ignore_errors=True)

    def find_same(self):
        item_dict = {}
        for k, v in self.mapping_table.items():
            if v not in item_dict:
                item_dict[v] = [k]
            else:
                item_dict[v].append(k)
        return item_dict

    def symlink_same_files(self):
        for k, v in self.find_same().items():
            if k is None:
                logger.debug(f"items not created by requre: {v}")
            if len(v) == 1:
                logger.debug(f"no duplication found: {v}")
            else:
                main_file = v[0]
                relative_main = main_file.replace(self.path, "")
                rest_files = v[1:]
                for file in rest_files:
                    if os.path.islink(file):
                        logger.debug(
                            f"{file} already symlinked to {os.path.realpath(file)}"
                        )
                        continue
                    relative_file = file.replace(self.path, "")
                    dir_deep = len(
                        os.path.dirname(relative_file)
                        .strip(os.path.sep)
                        .split(os.path.sep)
                    )
                    main_relative_file = f"..{os.path.sep}" * dir_deep + relative_main
                    os.remove(file)
                    os.symlink(main_relative_file, file)

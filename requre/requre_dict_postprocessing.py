import logging
from typing import Union, Any, Dict, Optional, List
from .constants import KEY_MINIMAL_MATCH, METATADA_KEY
from .storage import DataMiner, DataStructure

logger = logging.getLogger(__name__)


class DictProcessing:
    def __init__(self, requre_dict: dict):
        self.requre_dict = requre_dict

    def match(self, selector: list, internal_object: Union[dict, list, None] = None):
        if internal_object is None:
            internal_object = self.requre_dict
        if len(selector) == 0:
            logger.debug(f"all selectors matched")
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
    def minimal_match(dict_obj: Dict):
        tmp_dict = dict_obj
        for cntr in range(KEY_MINIMAL_MATCH):
            if not isinstance(tmp_dict, dict) or len(tmp_dict.keys()) != 1:
                return False
            key = list(tmp_dict.keys())[0]
            value = tmp_dict[key]
            tmp_dict = value
        if isinstance(tmp_dict, list):
            first_item = tmp_dict[0]
            if isinstance(
                first_item, dict
            ) and DataMiner().LATENCY_KEY in first_item.get(
                DataStructure.METADATA_KEY, {}
            ):
                return True
            else:
                return False
        # FIXME: solve situation for other types than list type
        return False

    def simplify(
        self, internal_object: Optional[Dict] = None, ignore_list: Optional[List] = None
    ):
        if ignore_list is None:
            ignore_list = []
        if internal_object is None:
            internal_object = self.requre_dict
        if isinstance(internal_object, dict):
            if len(internal_object.keys()) == 1:
                key = list(internal_object.keys())[0]
                if key in [METATADA_KEY] + ignore_list:
                    return
                if self.minimal_match(internal_object):
                    return
                if isinstance(internal_object[key], dict):
                    value = internal_object.pop(key)
                    print(
                        f"Removing key: {key}  and continue with {list(value.keys())}"
                    )
                    for k, v in value.items():
                        internal_object[k] = v
                        self.simplify(
                            internal_object=internal_object, ignore_list=ignore_list
                        )
            else:
                for v in internal_object.values():
                    self.simplify(internal_object=v, ignore_list=ignore_list)

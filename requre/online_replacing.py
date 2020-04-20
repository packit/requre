import sys
import re
import functools
import logging
from typing import List, Callable, Optional, Dict

from requre.storage import PersistentObjectStorage

logger = logging.getLogger(__name__)


def replace(
    in_module: str,
    what: str,
    decorate: Optional[Callable] = None,
    replace: Optional[Callable] = None,
    storage_file: Optional[str] = None,
):
    if (decorate is None and replace is None) or (
        decorate is not None and replace is not None
    ):
        raise ValueError("right one from [decorate, replace] parameter has to be set.")

    def decorator_cover(func):
        @functools.wraps(func)
        def _internal(*args, **kwargs):
            original_storage = None
            if storage_file:
                original_storage = PersistentObjectStorage().storage_file
                PersistentObjectStorage().storage_file = storage_file
            original_module_items: Dict[List] = {}
            for module_name, module in sys.modules.items():
                if not re.search(in_module, module_name):
                    continue
                logger.info(f"\nMATCHED MODULE: {module_name} by {in_module}")

                if len(what) > 0:
                    original_obj = module
                    parent_obj = original_obj
                    # trace into object structyre and get these objects
                    for key_item in what.split("."):
                        parent_obj = original_obj
                        original_obj = getattr(original_obj, key_item)
                    if replace is not None:
                        setattr(
                            parent_obj, original_obj.__name__, replace,
                        )
                        logger.info(
                            f"\treplacing {module_name}.{what}"
                            f" by function {replace.__name__}"
                        )
                    elif decorate is not None:
                        setattr(
                            parent_obj, original_obj.__name__, decorate(original_obj),
                        )
                        logger.info(
                            f"\tdecorating {module_name}.{what}"
                            f" by function {decorate.__name__}"
                        )
                    original_module_items[module_name] = [
                        what,
                        parent_obj,
                        original_obj,
                    ]
                else:
                    raise ValueError(
                        "You have to define what will be replaced inside module,"
                        " not possible to replace whole module on the fly"
                    )
            # execute content

            output = func(*args, **kwargs)

            # revert back
            for module_name, item_list in original_module_items.items():
                setattr(item_list[1], item_list[2].__name__, item_list[2])
            if original_storage:
                PersistentObjectStorage().storage_file = original_storage
            return output

        return _internal

    return decorator_cover

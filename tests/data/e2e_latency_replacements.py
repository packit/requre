from requre.import_system import ReplaceType
from requre.helpers.function_output import store_function_output

FILTERS: list = [
    ("^time$", {}, {"sleep": [ReplaceType.DECORATOR, store_function_output]})
]

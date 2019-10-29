from requre.import_system import ReplaceType
from requre.helpers.simple_object import Simple

FILTERS: list = [
    ("^time$", {}, {"sleep": [ReplaceType.DECORATOR, Simple.decorator_plain]})
]

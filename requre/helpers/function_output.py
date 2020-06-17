import warnings
from .simple_object import Simple

warnings.warn(
    "DEPRECATED: Please use Simple.decorator_plain from requre.helpers.simple_object"
)
store_function_output = Simple.decorator_plain()

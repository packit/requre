from requre.import_system import upgrade_import_system
from requre.helpers.simple_object import Simple

FILTERS = upgrade_import_system().decorate(
    where="^time$", what="sleep", who_name=[], decorator=Simple.decorator_plain
)

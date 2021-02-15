from requre.import_system import UpgradeImportSystem
from requre.helpers.simple_object import Simple

FILTERS = UpgradeImportSystem().decorate("time.sleep", Simple.decorator_plain())

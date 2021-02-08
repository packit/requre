from requre.import_system import UpgradeImportSystem
from requre.helpers.tempfile import TempFile

special = UpgradeImportSystem().decorate("tempfile.mktemp", TempFile.mktemp())

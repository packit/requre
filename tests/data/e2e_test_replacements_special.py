from requre.import_system import ReplaceType
from requre.helpers.tempfile import TempFile

special: list = [("^tempfile$", {}, {"": [ReplaceType.REPLACE_MODULE, TempFile]})]

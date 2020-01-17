from requre.helpers.files import StoreFiles
from requre.storage import PersistentObjectStorage
from tempfile import mkdtemp
import os

PersistentObjectStorage().storage_file = "files.yaml"
temp_file = mkdtemp()


@StoreFiles.guess_args
def return_result(value, dir_name):
    with open(os.path.join(dir_name, value), "w") as fd:
        fd.write(input("value: "))


value = return_result("filee", temp_file)

PersistentObjectStorage().dump()
print(PersistentObjectStorage().storage_object)
print(value)

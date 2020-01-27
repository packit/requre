from requre.helpers.files import StoreFiles
from requre.storage import PersistentObjectStorage
from tempfile import mkdtemp
import os

PersistentObjectStorage().storage_file = "files.yaml"
temp_dir = mkdtemp()


@StoreFiles.guess_args
def return_result(dir_name):
    file_name = input("enter file name: ")
    with open(os.path.join(dir_name, file_name), "w") as fd:
        fd.write("empty")
    return file_name


print("returned file name:", return_result(temp_dir))
print("dir name (current):", temp_dir)
print("files:", os.listdir(temp_dir))
PersistentObjectStorage().dump()

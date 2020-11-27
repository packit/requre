from requre.helpers.files import StoreFiles
from requre.cassette import Cassette
from tempfile import mkdtemp
import os

cassette = Cassette()
cassette.storage_file = "/tmp/files.yaml"
temp_dir = mkdtemp()


@StoreFiles.where_arg_references(
    key_position_params_dict={"dir_name": 0}, cassette=cassette
)
def return_result(dir_name):
    file_name = input("enter file name: ")
    with open(os.path.join(dir_name, file_name), "w") as fd:
        fd.write("empty")
    return file_name


print("returned file name:", return_result(temp_dir))
print("dir name (current):", temp_dir)
print("files:", os.listdir(temp_dir))
cassette.dump()

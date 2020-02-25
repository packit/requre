import os
import inspect
from unittest import TestCase
from requre.storage import PersistentObjectStorage
from requre.constants import RELATIVE_TEST_DATA_DIRECTORY


class RequreTestCase(TestCase):
    """
    This is base unittest TestCase what will help you to store requre storage files
    It will create directory structre test_data/TEST_FILE_NAME in a directory where
    test is stored. inside this subdir. there is created storage file via calling
    self.id()
    suffixed by yaml
    """

    def get_datafile_filename(self, suffix="yaml"):
        current_class_file = inspect.getfile(self.__class__)
        real_path_dir = os.path.realpath(os.path.dirname(current_class_file))
        test_file_name = os.path.basename(current_class_file).rsplit(".", 1)[0]
        test_name = self.id()
        testdata_dirname = os.path.join(
            real_path_dir, RELATIVE_TEST_DATA_DIRECTORY, test_file_name
        )
        return os.path.join(testdata_dirname, f"{test_name}.{suffix}")

    def setUp(self):
        super().setUp()
        response_file = self.get_datafile_filename()
        os.makedirs(os.path.dirname(response_file), mode=0o777, exist_ok=True)
        PersistentObjectStorage().storage_file = response_file

    def tearDown(self):
        PersistentObjectStorage().dump()
        super().tearDown()

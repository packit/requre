import os
import shutil
import tempfile
import unittest

from requre.storage import PersistentObjectStorage
from requre.utils import StorageMode


class BaseClass(unittest.TestCase):
    def setUp(self) -> None:
        PersistentObjectStorage().mode = StorageMode.default
        super().setUp()
        self.file_name = None
        self.temp_dir = None
        self.temp_file = None
        self.response_dir = tempfile.mkdtemp(prefix="data_store")
        self.response_file = os.path.join(self.response_dir, "storage_test.yaml")
        PersistentObjectStorage().storage_file = self.response_file
        PersistentObjectStorage().dump_after_store = True

    def tearDown(self) -> None:
        super().tearDown()
        shutil.rmtree(self.response_dir)
        if self.file_name:
            os.remove(self.file_name)
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if self.temp_file and os.path.exists(self.temp_file):
            os.remove(self.temp_file)

    def create_temp_dir(self):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
        self.temp_dir = tempfile.mkdtemp()

    def create_temp_file(self):
        if self.temp_file:
            os.remove(self.temp_file)
        self.temp_file = tempfile.mktemp()

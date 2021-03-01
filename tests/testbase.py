import os
import shutil
import tempfile
import unittest
import socket

from requre.storage import PersistentObjectStorage
from requre.utils import StorageMode

EXAMPLE_COM_IP = "93.184.216.34"


class RetTuple:
    def ret(self, value):
        return "ret", value


def network_connection_available():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sock.connect_ex((EXAMPLE_COM_IP, 80)) == 0:
        return True
    return False


class BaseClass(unittest.TestCase):
    def setUp(self) -> None:
        self.cassette = PersistentObjectStorage().cassette
        self.cassette.storage_file = None
        self.cassette.mode = StorageMode.default
        super().setUp()
        self.file_name = None
        self.temp_dir = None
        self.temp_file = None
        self.response_dir = tempfile.mkdtemp(prefix="data_store")
        self.response_file = os.path.join(self.response_dir, "storage_test.yaml")
        self.cassette.storage_file = self.response_file
        self.cassette.dump_after_store = True

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

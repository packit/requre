import os
import tempfile
import shutil
import yaml
from unittest import TestCase
from requre.constants import ENV_REQURE_STORAGE_MODE
from requre.exceptions import PersistentStorageException
from requre.storage import PersistentObjectStorage
from requre.cassette import StorageMode


class GenericModeTests(TestCase):
    def tearDown(self) -> None:
        if ENV_REQURE_STORAGE_MODE in os.environ:
            del os.environ[ENV_REQURE_STORAGE_MODE]
        super().tearDown()

    def test_bad_mode(self):
        os.environ[ENV_REQURE_STORAGE_MODE] = "mistake"
        with self.assertRaises(PersistentStorageException) as context:
            PersistentObjectStorage().cassette.storage_file = "/not/important"
            self.assertTrue("storage mode mistake does not exist," in context.exception)

    def test_default(self):
        PersistentObjectStorage().cassette._set_defaults()
        self.assertEqual(PersistentObjectStorage().cassette.mode, StorageMode.default)


class ReadMode(TestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ[ENV_REQURE_STORAGE_MODE] = "read"
        self.response_dir = tempfile.mkdtemp(prefix="data_store")
        self.response_file = os.path.join(self.response_dir, "storage_test.yaml")

    def tearDown(self) -> None:
        shutil.rmtree(self.response_dir)
        if ENV_REQURE_STORAGE_MODE in os.environ:
            del os.environ[ENV_REQURE_STORAGE_MODE]
        super().tearDown()

    def test_existing_file(self):
        with open(self.response_file, "w") as fd:
            yaml.dump({}, fd)
        PersistentObjectStorage().cassette.storage_file = self.response_file
        self.assertEqual(PersistentObjectStorage().cassette.mode, StorageMode.read)

    def test_non_existing_file(self):
        with self.assertRaises(PersistentStorageException) as context:
            PersistentObjectStorage().cassette.storage_file = self.response_file
            self.assertTrue("does not exist" in context.exception)


class WriteMode(TestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ[ENV_REQURE_STORAGE_MODE] = "write"
        self.response_dir = tempfile.mkdtemp(prefix="data_store")
        self.response_file = os.path.join(self.response_dir, "storage_test.yaml")

    def tearDown(self) -> None:
        shutil.rmtree(self.response_dir)
        if ENV_REQURE_STORAGE_MODE in os.environ:
            del os.environ[ENV_REQURE_STORAGE_MODE]
        super().tearDown()

    def test_existing_file(self):
        with open(self.response_file, "w") as fd:
            yaml.dump({}, fd)
        PersistentObjectStorage().cassette.storage_file = self.response_file
        self.assertEqual(PersistentObjectStorage().cassette.mode, StorageMode.write)

    def test_non_existing_file(self):
        PersistentObjectStorage().cassette.storage_file = self.response_file


class AppendMode(WriteMode):
    def setUp(self) -> None:
        super().setUp()
        os.environ[ENV_REQURE_STORAGE_MODE] = "append"

    def test_existing_file(self):
        with open(self.response_file, "w") as fd:
            yaml.dump({}, fd)
        PersistentObjectStorage().cassette.storage_file = self.response_file
        self.assertEqual(PersistentObjectStorage().cassette.mode, StorageMode.append)

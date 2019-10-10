import os
from requre.utils import STORAGE
from requre.exceptions import PersistentStorageException
from tests.testbase import BaseClass


class Base(BaseClass):
    keys = ["a", "b"]

    def setUp(self) -> None:
        super().setUp()
        STORAGE.dump_after_store = False

    def store_keys_example(self):
        STORAGE.store(self.keys, values="c")
        STORAGE.store(self.keys, values="d")

    def test_simple(self):
        self.store_keys_example()
        self.assertEqual("c", STORAGE.read(self.keys))
        self.assertEqual("d", STORAGE.read(self.keys))

    def test_exception(self):
        self.test_simple()
        self.assertRaises(PersistentStorageException, STORAGE.read, self.keys)

    def test_write(self):
        self.store_keys_example()
        self.assertFalse(os.path.exists(self.response_file))
        STORAGE.dump()
        self.assertTrue(os.path.exists(self.response_file))


class Versioning(BaseClass):
    def setUp(self) -> None:

        super().setUp()
        STORAGE.dump_after_store = False

    def test(self):
        """
        Check if storage is able to read and write version to persistent storage file
        """
        self.assertEqual({}, STORAGE.requre_internal_object)
        self.assertEqual(0, STORAGE.storage_file_version)
        self.assertFalse(os.path.exists(self.response_file))
        STORAGE.dump()
        self.assertTrue(os.path.exists(self.response_file))
        self.assertEqual(1, STORAGE.storage_file_version)
        self.assertNotEqual({}, STORAGE.requre_internal_object)
        STORAGE.storage_object = {}
        self.assertEqual({}, STORAGE.requre_internal_object)
        self.assertEqual(0, STORAGE.storage_file_version)
        STORAGE.load()
        self.assertEqual(1, STORAGE.storage_file_version)
        self.assertNotEqual({}, STORAGE.requre_internal_object)
        self.assertIn("version_storage_file", STORAGE.requre_internal_object)

import os
import time
from requre.utils import STORAGE
from requre.constants import VERSION_REQURE_FILE
from requre.exceptions import PersistentStorageException
from requre.storage import DataMiner, DataTypes
from tests.testbase import BaseClass


class Base(BaseClass):
    keys = ["a", "b"]

    def setUp(self) -> None:
        super().setUp()
        STORAGE.dump_after_store = False

    def store_keys_example(self):
        STORAGE.store(self.keys, values="c", metadata={})
        STORAGE.store(self.keys, values="d", metadata={})

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

    def test_no_version(self):
        """
        Check if storage is able to read and write version to persistent storage file
        """
        self.assertEqual({}, STORAGE.metadata)
        self.assertEqual(0, STORAGE.storage_file_version)
        self.assertEqual(None, STORAGE.metadata.get(STORAGE.version_key))
        self.assertFalse(os.path.exists(self.response_file))

    def test_no_version_after_dump(self):
        STORAGE.dump()
        STORAGE.storage_object = {}
        self.assertEqual({}, STORAGE.metadata)
        self.assertEqual(0, STORAGE.storage_file_version)

    def test_current_version(self):
        STORAGE.dump()
        self.assertTrue(os.path.exists(self.response_file))
        self.assertEqual(VERSION_REQURE_FILE, STORAGE.storage_file_version)
        self.assertNotEqual({}, STORAGE.metadata)

    def test_current_version_after_load(self):
        STORAGE.dump()
        STORAGE.load()
        self.assertEqual(VERSION_REQURE_FILE, STORAGE.storage_file_version)
        self.assertNotEqual({}, STORAGE.metadata)
        self.assertIn("version_storage_file", STORAGE.metadata)


class TestStoreTypes(BaseClass):
    keys = ["a", "b"]

    def tearDown(self):
        DataMiner().data_type = DataTypes.List

    def test_default(self):
        self.assertEqual(DataTypes.List, DataMiner().data_type)

    def test_list_data(self):
        STORAGE.store(keys=self.keys, values="x", metadata={})
        STORAGE.store(keys=self.keys, values="y", metadata={})
        self.assertEqual(2, len(STORAGE.storage_object["a"]["b"]))
        self.assertEqual("x", STORAGE.read(keys=self.keys))
        self.assertEqual(1, len(STORAGE.storage_object["a"]["b"]))
        self.assertEqual("y", STORAGE.read(keys=self.keys))
        self.assertEqual(0, len(STORAGE.storage_object["a"]["b"]))

    def test_dict_data(self):
        DataMiner().data_type = DataTypes.Dict
        STORAGE.store(keys=self.keys, values="x", metadata={})
        STORAGE.store(keys=self.keys, values="y", metadata={})
        self.assertEqual(2, len(STORAGE.storage_object["a"]["b"]))
        self.assertEqual("y", STORAGE.read(keys=self.keys))
        self.assertEqual(2, len(STORAGE.storage_object["a"]["b"]))
        self.assertEqual("y", STORAGE.read(keys=self.keys))
        self.assertEqual(2, len(STORAGE.storage_object["a"]["b"]))


class Metadata(BaseClass):
    keys = ["a", "b"]

    def setUp(self):
        super().setUp()
        DataMiner().current_time = time.time()

    def test_latency(self):
        delta = 0.05

        STORAGE.store(keys=self.keys, values="x", metadata={})
        self.assertAlmostEqual(
            0, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )
        # Try to set some custom metadata
        DataMiner().data.metadata = {"random": "data"}

        time.sleep(0.1)
        STORAGE.store(keys=self.keys, values="y", metadata={})
        self.assertAlmostEqual(
            0.1, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )

        time.sleep(0.2)
        STORAGE.store(keys=self.keys, values="z", metadata={})
        self.assertAlmostEqual(
            0.2, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )

        STORAGE.read(keys=self.keys)
        self.assertAlmostEqual(
            0, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )
        # check custom metadata
        self.assertEqual("data", DataMiner().metadata["random"])

        STORAGE.read(keys=self.keys)
        self.assertAlmostEqual(
            0.1, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )
        # check if custom metadata are not everywhere
        self.assertNotIn("random", DataMiner().metadata)
        self.assertIn("latency", DataMiner().metadata)

        STORAGE.read(keys=self.keys)
        self.assertAlmostEqual(
            0.2, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )

    def test_generic(self):
        STORAGE.store(keys=self.keys, values="x", metadata={"test_meta": "yes"})
        STORAGE.metadata = {"rpms": ["package1", "package2"]}
        STORAGE.dump()
        STORAGE.storage_object = {}
        STORAGE.load()
        STORAGE.read(keys=self.keys)
        self.assertEqual(DataMiner().metadata["test_meta"], "yes")
        self.assertEqual(STORAGE.metadata.get(STORAGE.key_inspect_strategy_key), 1)
        self.assertEqual(STORAGE.metadata.get("rpms"), ["package1", "package2"])


class Latency(BaseClass):
    keys = ["a", "b"]

    def setUp(self):
        super().setUp()
        DataMiner().current_time = time.time()
        DataMiner().use_latency = True

    def tearDown(self):
        DataMiner().use_latency = False

    def test_not_applied(self):
        DataMiner().use_latency = False
        delta = 0.05
        STORAGE.store(keys=self.keys, values="x", metadata={})
        time.sleep(0.2)
        STORAGE.store(keys=self.keys, values="y", metadata={})
        self.assertAlmostEqual(
            0.2, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )

        time_begin = time.time()
        STORAGE.read(keys=self.keys)
        time_end = time.time()
        self.assertAlmostEqual(0, time_end - time_begin, delta=delta)

        time_begin = time.time()
        STORAGE.read(keys=self.keys)
        time_end = time.time()
        self.assertAlmostEqual(0, time_end - time_begin, delta=delta)

    def test_applied(self):
        delta = 0.05
        STORAGE.store(keys=self.keys, values="x", metadata={})
        time.sleep(0.2)
        STORAGE.store(keys=self.keys, values="y", metadata={})
        self.assertAlmostEqual(
            0.2, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )

        time_begin = time.time()
        STORAGE.read(keys=self.keys)
        time_end = time.time()
        self.assertAlmostEqual(0, time_end - time_begin, delta=delta)

        time_begin = time.time()
        STORAGE.read(keys=self.keys)
        time_end = time.time()
        self.assertAlmostEqual(0.2, time_end - time_begin, delta=delta)

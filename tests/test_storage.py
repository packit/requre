import os
import time

from requre.constants import VERSION_REQURE_FILE
from requre.exceptions import PersistentStorageException
from requre.helpers.simple_object import Simple

from requre.cassette import (
    DataTypes,
    StorageKeysInspectDefault,
    StorageKeysInspectSimple,
    StorageKeysInspect,
    StorageKeysInspectUnique,
)
from requre.utils import StorageMode
from tests.testbase import BaseClass


class Base(BaseClass):
    keys = ["a", "b"]

    def setUp(self) -> None:
        super().setUp()
        self.cassette.dump_after_store = False

    def store_keys_example(self):
        self.cassette.store(self.keys, values="c", metadata={})
        self.cassette.store(self.keys, values="d", metadata={})

    def test_simple(self):
        self.store_keys_example()
        self.assertEqual("c", self.cassette[self.keys])
        self.assertEqual("d", self.cassette[self.keys])

    def test_exception(self):
        self.test_simple()
        self.assertRaises(PersistentStorageException, self.cassette.read, self.keys)

    def test_write(self):
        self.store_keys_example()
        self.assertFalse(os.path.exists(self.response_file))
        self.cassette.dump()
        self.assertTrue(os.path.exists(self.response_file))


class Versioning(BaseClass):
    def setUp(self) -> None:
        super().setUp()
        self.cassette.dump_after_store = False

    def test_no_version(self):
        """
        Check if storage is able to read and write version to persistent storage file
        """
        self.assertEqual({}, self.cassette.metadata)
        self.assertEqual(0, self.cassette.storage_file_version)
        self.assertEqual(
            None,
            self.cassette.metadata.get(self.cassette.version_key),
        )
        self.assertFalse(os.path.exists(self.response_file))

    def test_no_version_after_dump(self):
        self.cassette.dump()
        self.cassette.storage_object = {}
        self.assertEqual({}, self.cassette.metadata)
        self.assertEqual(0, self.cassette.storage_file_version)

    def test_current_version(self):
        self.cassette.dump()
        self.assertTrue(os.path.exists(self.response_file))
        self.assertEqual(VERSION_REQURE_FILE, self.cassette.storage_file_version)
        self.assertNotEqual({}, self.cassette.metadata)

    def test_current_version_after_load(self):
        self.cassette.dump()
        self.cassette.load()
        self.assertEqual(VERSION_REQURE_FILE, self.cassette.storage_file_version)
        self.assertNotEqual({}, self.cassette.metadata)
        self.assertIn("version_storage_file", self.cassette.metadata)


class TestStoreTypes(BaseClass):
    keys = ["a", "b"]

    def tearDown(self):
        self.cassette.data_miner.data_type = DataTypes.List

    def test_default(self):
        self.assertEqual(DataTypes.List, self.cassette.data_miner.data_type)

    def test_list_data(self):
        self.cassette.store(keys=self.keys, values="x", metadata={})
        self.cassette.store(keys=self.keys, values="y", metadata={})
        self.assertEqual(2, len(self.cassette.storage_object["a"]["b"]))
        self.assertEqual("x", self.cassette[self.keys])
        self.assertEqual(1, len(self.cassette.storage_object["a"]["b"]))
        self.assertEqual("y", self.cassette[self.keys])
        self.assertEqual(0, len(self.cassette.storage_object["a"]["b"]))

    def test_value_data(self):
        self.cassette.data_miner.data_type = DataTypes.Value
        self.cassette.store(keys=self.keys, values="x", metadata={})
        self.cassette.store(keys=self.keys, values="y", metadata={})
        self.assertEqual(2, len(self.cassette.storage_object["a"]["b"]))
        self.assertEqual("y", self.cassette[self.keys])
        self.assertEqual(2, len(self.cassette.storage_object["a"]["b"]))
        self.assertEqual("y", self.cassette[self.keys])
        self.assertEqual(2, len(self.cassette.storage_object["a"]["b"]))

    def test_dict_data(self):
        self.cassette.data_miner.data_type = DataTypes.Dict
        self.cassette.data_miner.key = "first-key"
        self.cassette.store(keys=self.keys, values="x", metadata={})
        self.cassette.data_miner.key = "second-key"
        self.cassette.store(keys=self.keys, values="y", metadata={})

        self.assertIn("first-key", self.cassette.storage_object["a"]["b"])
        self.assertIn("second-key", self.cassette.storage_object["a"]["b"])

        self.assertEqual("y", self.cassette[self.keys])
        self.cassette.data_miner.key = "first-key"
        self.assertEqual("x", self.cassette[self.keys])

    def test_dict_with_list_data(self):
        self.cassette.data_miner.data_type = DataTypes.DictWithList
        self.cassette.data_miner.key = "first-key"
        self.cassette.store(keys=self.keys, values="x", metadata={})
        self.cassette.data_miner.key = "second-key"
        self.cassette.store(keys=self.keys, values="y", metadata={})
        self.cassette.store(keys=self.keys, values="z", metadata={})

        self.assertIn("first-key", self.cassette.storage_object["a"]["b"])
        self.assertIn("second-key", self.cassette.storage_object["a"]["b"])

        self.assertEqual("y", self.cassette[self.keys])
        self.assertEqual("z", self.cassette[self.keys])
        self.cassette.data_miner.key = "first-key"
        self.assertEqual("x", self.cassette[self.keys])


class Metadata(BaseClass):
    keys = ["a", "b"]

    @staticmethod
    @Simple.decorator_plain()
    def simple_return(value):
        return value

    def setUp(self):
        super().setUp()
        self.cassette.data_miner.current_time = time.time()

    def test_latency(self):
        delta = 0.05

        self.cassette.store(keys=self.keys, values="x", metadata={})
        self.assertAlmostEqual(
            0,
            self.cassette.data_miner.metadata[self.cassette.data_miner.LATENCY_KEY],
            delta=delta,
        )
        # Try to set some custom metadata
        self.cassette.data_miner.data.metadata = {"random": "data"}

        time.sleep(0.1)
        self.cassette.store(keys=self.keys, values="y", metadata={})
        self.assertAlmostEqual(
            0.1,
            self.cassette.data_miner.metadata[self.cassette.data_miner.LATENCY_KEY],
            delta=delta,
        )

        time.sleep(0.2)
        self.cassette.store(keys=self.keys, values="z", metadata={})
        self.assertAlmostEqual(
            0.2,
            self.cassette.data_miner.metadata[self.cassette.data_miner.LATENCY_KEY],
            delta=delta,
        )
        self.cassette.read(self.keys)
        self.assertAlmostEqual(
            0,
            self.cassette.data_miner.metadata[self.cassette.data_miner.LATENCY_KEY],
            delta=delta,
        )
        # check custom metadata
        self.assertEqual("data", self.cassette.data_miner.metadata["random"])

        self.cassette.read(self.keys)
        self.assertAlmostEqual(
            0.1,
            self.cassette.data_miner.metadata[self.cassette.data_miner.LATENCY_KEY],
            delta=delta,
        )
        # check if custom metadata are not everywhere
        self.assertNotIn("random", self.cassette.data_miner.metadata)
        self.assertIn("latency", self.cassette.data_miner.metadata)
        self.cassette.read(self.keys)
        self.assertAlmostEqual(
            0.2,
            self.cassette.data_miner.metadata[self.cassette.data_miner.LATENCY_KEY],
            delta=delta,
        )

    def test_generic(self):
        self.cassette.store(keys=self.keys, values="x", metadata={"test_meta": "yes"})
        self.cassette.metadata = {"rpms": ["package1", "package2"]}
        self.cassette.dump()
        self.cassette.storage_object = {}
        self.cassette.load()
        self.assertIn(self.keys, self.cassette)
        self.assertEqual(self.cassette.data_miner.metadata["test_meta"], "yes")
        self.assertEqual(
            self.cassette.metadata.get(self.cassette.key_inspect_strategy_key),
            StorageKeysInspectDefault.__name__,
        )
        self.assertEqual(self.cassette.metadata.get("rpms"), ["package1", "package2"])

    def test_strategy(self):
        self.cassette.data_miner.key_stategy_cls = StorageKeysInspectSimple
        self.cassette.store(keys=self.keys, values="x", metadata={})
        self.simple_return("ahoj")
        self.simple_return([1, 2, 3])

        self.cassette.dump()
        self.cassette.storage_object = {}
        self.cassette.data_miner.key_stategy_cls = StorageKeysInspectDefault
        self.cassette.mode = StorageMode.read
        self.cassette.load()
        self.assertEqual("x", self.cassette[self.keys])
        self.assertEqual(
            self.cassette.metadata.get(self.cassette.key_inspect_strategy_key),
            StorageKeysInspectSimple.__name__,
        )
        self.assertEqual(
            StorageKeysInspectSimple, self.cassette.data_miner.key_stategy_cls
        )

    def test_strategy_proper(self):
        self.test_strategy()
        self.cassette.load()
        print(self.cassette.storage_object)
        self.assertEqual("ahoj", self.simple_return("nonsense"))
        self.assertEqual([1, 2, 3], self.simple_return("nonsense"))

    def test_strategy_API_cls(self):
        self.test_strategy()
        self.cassette.load()
        self.cassette.data_miner.key_stategy_cls = StorageKeysInspect
        self.assertRaises(NotImplementedError, self.simple_return, "nonsense")

    def test_strategy_default_cls(self):
        self.test_strategy()
        self.cassette.load()
        self.cassette.data_miner.key_stategy_cls = StorageKeysInspectDefault
        self.assertEqual("ahoj", self.simple_return("nonsense"))

    def test_strategy_unique(self):
        keys = self.keys + ["c"] + self.keys + ["d"]
        self.assertEqual(
            StorageKeysInspectUnique._get_unique_keys(keys), ["c"] + self.keys + ["d"]
        )


class Latency(BaseClass):
    keys = ["a", "b"]

    def setUp(self):
        super().setUp()
        self.cassette.data_miner.current_time = time.time()
        self.cassette.data_miner.use_latency = True

    def tearDown(self):
        self.cassette.data_miner.use_latency = False

    def test_not_applied(self):
        self.cassette.data_miner.use_latency = False
        delta = 0.05
        self.cassette.store(keys=self.keys, values="x", metadata={})
        time.sleep(0.2)
        self.cassette.store(keys=self.keys, values="y", metadata={})
        self.assertAlmostEqual(
            0.2,
            self.cassette.data_miner.metadata[self.cassette.data_miner.LATENCY_KEY],
            delta=delta,
        )

        time_begin = time.time()
        self.assertIn(self.keys, self.cassette)
        time_end = time.time()
        self.assertAlmostEqual(0, time_end - time_begin, delta=delta)

        time_begin = time.time()
        self.assertIn(self.keys, self.cassette)
        time_end = time.time()
        self.assertAlmostEqual(0, time_end - time_begin, delta=delta)

    def test_applied(self):
        delta = 0.05
        self.cassette.store(keys=self.keys, values="x", metadata={})
        time.sleep(0.2)
        self.cassette.store(keys=self.keys, values="y", metadata={})
        self.assertAlmostEqual(
            0.2,
            self.cassette.data_miner.metadata[self.cassette.data_miner.LATENCY_KEY],
            delta=delta,
        )

        time_begin = time.time()
        self.cassette.read(self.keys)
        time_end = time.time()
        self.assertAlmostEqual(0, time_end - time_begin, delta=delta)

        time_begin = time.time()
        self.cassette.read(self.keys)
        time_end = time.time()
        self.assertAlmostEqual(0.2, time_end - time_begin, delta=delta)


class KeySkipping(BaseClass):
    """
    Check fault tolerancy of intermediate keys
    """

    keys = ["a", "b", "c", "d"]

    def setUp(self):
        super().setUp()
        self.cassette.store(keys=self.keys, values="x", metadata={})

    def tearDown(self):
        self.cassette.data_miner.read_key_exact = False

    def test_all_match(self):
        output = self.cassette.read(self.keys)
        self.assertEqual("x", output)

    def test_key_1_inserted(self):
        output = self.cassette.read(self.keys[:1] + ["y"] + self.keys[1:])
        self.assertEqual("x", output)

    def test_key_0_inserted(self):
        output = self.cassette.read(["y"] + self.keys)
        self.assertEqual("x", output)

    def test_key_inserted_2_before(self):
        output = self.cassette.read(self.keys[:-2] + ["y"] + self.keys[-2:])
        self.assertEqual("x", output)

    def test_key_inserted_last(self):
        self.assertRaises(
            PersistentStorageException,
            self.cassette.read,
            self.keys + ["y"],
        )

    def test_key_inserted_1_before(self):
        self.assertRaises(
            PersistentStorageException,
            self.cassette.read,
            self.keys[:-1] + ["y"] + self.keys[-1:],
        )

    def test_key_exact_miner(self):
        self.cassette.data_miner.read_key_exact = True
        output = self.cassette.read(self.keys)
        self.assertEqual("x", output)

    def test_key_exact_miner_exception(self):
        self.cassette.data_miner.read_key_exact = True
        self.assertRaises(
            PersistentStorageException,
            self.cassette.read,
            ["y"] + self.keys,
        )

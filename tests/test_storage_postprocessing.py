import os
import unittest
from copy import deepcopy
from requre.utils import run_command
from requre.postprocessing import DictProcessing
from requre.cassette import DataTypes
from tests.testbase import BaseClass
from tests.test_e2e_test_patching import is_requre_installed

CMD_TOOL = "requre-patch purge"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class ObjectPostprocessing(unittest.TestCase):
    def setUp(self) -> None:
        self.testDict = {
            "a": {"b": {"c": "ahoj"}},
            "int": 2,
            "str": "anystr",
            "bool": False,
            "list": [1, 2, {"a": "y"}],
            "list_inside": [{"m": {"n": "o"}}],
            "dict": {"a": "x"},
        }
        self.dp = DictProcessing(self.testDict)

    def testMatchNoSelector(self):
        self.assertEqual(1, len(list(self.dp.match([]))))

    def testMatchMultiSelector(self):
        self.assertEqual(3, len(list(self.dp.match(["a"]))))

    def testMatchDeep(self):
        output = list(self.dp.match(["list_inside", "m"]))
        self.assertEqual(1, len(output))
        self.assertEqual({"n": "o"}, output[0])

        output = list(self.dp.match(["n"]))
        self.assertEqual(1, len(output))
        self.assertEqual("o", output[0])

    def testMatchNoMatch(self):
        self.assertEqual(0, len(list(self.dp.match(["non_sense"]))))

    def testReplaceMulti(self):
        tmp_dict = deepcopy(self.testDict)
        DictProcessing.replace(self.testDict, "a", "some")
        self.assertEqual(self.testDict["a"], "some")
        self.assertEqual(self.testDict["dict"]["a"], "some")
        self.assertEqual(self.testDict["list"][2]["a"], "some")
        self.assertNotEqual(tmp_dict, self.testDict)

    def testReplaceNone(self):
        tmp_dict = deepcopy(self.testDict)
        DictProcessing.replace(self.testDict, "nonsense", "some")
        self.assertEqual(tmp_dict, self.testDict)


@unittest.skipUnless(
    is_requre_installed(), "not possible to run without installed requre"
)
class FilePostprocessing(unittest.TestCase):
    storage_file = os.path.join(DATA_DIR, "requre_postprocessing.yaml")
    storage_file_tmp = storage_file + ".tmp"

    def setUp(self) -> None:
        run_command(cmd=f"cp {self.storage_file} {self.storage_file_tmp}")

    def tearDown(self) -> None:
        run_command(cmd=f"rm {self.storage_file_tmp}")

    def testOutput(self):
        replacement = (
            "tests_requre.openshift_integration.test_fedpkg.FedPkg."
            "test_fedpkg_clone.yaml:output:str:random_output"
        )
        run_command(f"{CMD_TOOL} --replaces {replacement} {self.storage_file_tmp}")
        with open(self.storage_file_tmp, mode="r") as opened_file:
            output = opened_file.read()
            self.assertIn("random_output", output)
            self.assertIn("requre.openshift_integration", output)
            self.assertIn("latency: xxxx", output)
            self.assertNotIn("output: yyy", output)

    def testLatency(self):
        replacement = "clone%store_function_output:latency:int:50"
        run_command(f"{CMD_TOOL} --replaces {replacement} {self.storage_file_tmp}")
        with open(self.storage_file_tmp, mode="r") as opened_file:
            output = opened_file.read()
            self.assertNotIn("random_output", output)
            self.assertIn("requre.openshift_integration", output)
            self.assertNotIn("latency: xxxx", output)
            self.assertIn("output: yyy", output)
            self.assertIn("latency: 0", output)
            self.assertIn("latency: 50", output)

    def testReplaceAll(self):
        replacement = ":latency:int:50"
        output = run_command(
            f"{CMD_TOOL} --replaces {replacement} {self.storage_file_tmp}", output=True
        )
        print(output)
        with open(self.storage_file_tmp, mode="r") as opened_file:
            output = opened_file.read()
            self.assertNotIn("random_output", output)
            self.assertIn("requre.openshift_integration", output)
            self.assertNotIn("latency: xxxx", output)
            self.assertIn("output: yyy", output)
            self.assertNotIn("latency: 0", output)
            self.assertIn("latency: 50", output)


class Simplify(BaseClass):
    """
    Check simplifying of keys
    """

    keys = ["a", "b", "c", "d", "e"]
    metadata = {"latency": 0}

    def tearDown(self):
        # return it to default type
        self.cassette.data_type = DataTypes.List
        super().tearDown()

    def store_key(self):
        self.cassette.store(keys=self.keys, values="x", metadata=self.metadata)

    def testDefault(self):
        self.store_key()
        processor = DictProcessing(self.cassette.storage_object)
        processor.simplify()
        self.assertIn("'a': {'d': {'e': [", str(self.cassette.storage_object))

    def testDict(self):
        self.cassette.data_miner.data_type = DataTypes.Dict
        self.store_key()
        processor = DictProcessing(self.cassette.storage_object)
        processor.simplify()
        self.assertIn(
            "'a': {'d': {'e': {'%s': {'metadata'" % self.cassette.data_miner.key,
            str(self.cassette.storage_object),
        )

    def testDictWithList(self):
        self.cassette.data_miner.data_type = DataTypes.DictWithList
        self.store_key()
        print(self.cassette.storage_object)
        processor = DictProcessing(self.cassette.storage_object)
        processor.simplify()
        self.assertIn(
            "'a': {'d': {'e': {'%s': [" % self.cassette.data_miner.key,
            str(self.cassette.storage_object),
        )

    def testValue(self):
        self.cassette.data_miner.data_type = DataTypes.Value
        self.store_key()
        print(self.cassette.storage_object)
        processor = DictProcessing(self.cassette.storage_object)
        processor.simplify()
        self.assertIn(
            "'a': {'d': {'e': {'metadata'",
            str(self.cassette.storage_object),
        )

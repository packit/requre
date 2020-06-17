from requre.objects import ObjectStorage
from requre.utils import StorageMode

from tests.testbase import BaseClass


class OwnClass:
    def __init__(self, num):
        self.num = num

    def get_num(self, return_num, extended=False):
        if extended:
            return f"{return_num}"
        else:
            return return_num

    def get_sum(self, inputval):
        return self.num + inputval


class StoreAnyRequest(BaseClass):
    domain = "https://example.com/"

    def testRawCall(self):
        """
        Test if is class is able to explicitly write and read object handling
        """
        keys = [1]
        sess = ObjectStorage(store_keys=keys, cassette=self.cassette)
        obj_before = OwnClass(*keys)
        sess.write(obj_before)
        obj_after = sess.read()
        self.assertIsInstance(obj_before, OwnClass)
        # it depickle object but object has not be same
        self.assertNotEqual(obj_before, obj_after)
        self.assertEqual(obj_before.num, obj_after.num)
        self.assertEqual(obj_after.num, 1)

    def testExecuteWrapper(self):
        """
        test if it is able to use explicit decorator_all_keys for storing object handling
        :return:
        """
        obj_before = ObjectStorage.execute_all_keys(OwnClass, 1, cassette=self.cassette)
        self.cassette.dump()
        self.cassette.mode = StorageMode.read
        obj_after = ObjectStorage.execute_all_keys(OwnClass, 1, cassette=self.cassette)
        self.assertEqual(obj_before.num, obj_after.num)
        # all objects are already read, next have to fail
        self.assertRaises(
            Exception,
            ObjectStorage.execute_all_keys,
            OwnClass,
            1,
            cassette=self.cassette,
        )

    def testFunctionDecorator(self):
        """
        Test main purpose of the class, decorate class and use it then
        """
        decorated_own = ObjectStorage.decorator_all_keys()(OwnClass)
        obj_before = decorated_own(1)
        self.cassette.dump()
        self.cassette.mode = StorageMode.read
        obj_after = decorated_own(1)
        self.assertEqual(obj_before.num, obj_after.num)
        # all objects are already read, next have to fail
        self.assertRaises(Exception, decorated_own, 1)


class CallDebug(BaseClass):
    def setUp(self) -> None:
        super().setUp()
        self.cassette.data_miner.store_arg_debug_metadata = True

    def tearDown(self) -> None:
        self.cassette.data_miner.store_arg_debug_metadata = False
        super().tearDown()

    def testCallDebug(self):
        OwnClass.get_num = ObjectStorage.decorator_plain()(OwnClass.get_num)
        test_obj = OwnClass(3)
        obj_before_4 = test_obj.get_num(4)
        obj_before_5 = test_obj.get_num(5, extended=True)
        self.cassette.dump()
        self.cassette.mode = StorageMode.read
        obj_after_4 = test_obj.get_num(4)
        obj_after_4_meta = self.cassette.data_miner.metadata
        obj_after_5 = test_obj.get_num(5, extended=True)
        obj_after_5_meta = self.cassette.data_miner.metadata
        self.assertEqual(obj_before_4, obj_after_4)
        self.assertIsInstance(obj_after_4, int)
        self.assertRegex(
            obj_after_4_meta[self.cassette.data_miner.METADATA_ARG_DEBUG_KEY],
            "get_num(.*, 4)",
        )
        self.assertEqual(obj_before_5, obj_after_5)
        self.assertIsInstance(obj_after_5, str)
        self.assertRegex(
            obj_after_5_meta[self.cassette.data_miner.METADATA_ARG_DEBUG_KEY],
            "get_num(.*, 5, extended=True)",
        )

    def testCallNoDebug(self):
        self.cassette.data_miner.store_arg_debug_metadata = False
        OwnClass.get_num = ObjectStorage.decorator_plain()(OwnClass.get_num)
        test_obj = OwnClass(3)
        obj_before_4 = test_obj.get_num(4)
        obj_sum_before = test_obj.get_sum(3)
        self.cassette.dump()
        self.cassette.mode = StorageMode.read
        obj_after_4 = test_obj.get_num(4)
        obj_sum_after = test_obj.get_sum(3)
        obj_after_4_meta = self.cassette.data_miner.metadata
        self.assertEqual(obj_sum_before, 6)
        self.assertEqual(obj_sum_after, 6)
        self.assertEqual(obj_before_4, obj_after_4)
        self.assertIsInstance(obj_after_4, int)
        self.assertEqual(
            obj_after_4_meta.get(self.cassette.data_miner.METADATA_ARG_DEBUG_KEY), None
        )

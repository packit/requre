from requre.objects import ObjectStorage
from requre.storage import PersistentObjectStorage, DataMiner
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


class StoreAnyRequest(BaseClass):
    domain = "https://example.com/"

    def testRawCall(self):
        """
        Test if is class is able to explicitly write and read object handling
        """
        keys = [1]
        sess = ObjectStorage(store_keys=keys)
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
        obj_before = ObjectStorage.execute_all_keys(OwnClass, 1)
        PersistentObjectStorage().dump()
        PersistentObjectStorage().mode = StorageMode.read
        obj_after = ObjectStorage.execute_all_keys(OwnClass, 1)
        self.assertEqual(obj_before.num, obj_after.num)
        # all objects are already read, next have to fail
        self.assertRaises(Exception, ObjectStorage.execute_all_keys, OwnClass, 1)

    def testFunctionDecorator(self):
        """
        Test main purpose of the class, decorate class and use it then
        """
        decorated_own = ObjectStorage.decorator_all_keys(OwnClass)
        obj_before = decorated_own(1)
        PersistentObjectStorage().dump()
        PersistentObjectStorage().mode = StorageMode.read
        obj_after = decorated_own(1)
        self.assertEqual(obj_before.num, obj_after.num)
        # all objects are already read, next have to fail
        self.assertRaises(Exception, decorated_own, 1)


class CallDebug(BaseClass):
    def setUp(self) -> None:
        super().setUp()
        DataMiner().store_arg_debug_metadata = True

    def tearDown(self) -> None:
        DataMiner().store_arg_debug_metadata = False
        super().tearDown()

    def testCallDebug(self):
        OwnClass.get_num = ObjectStorage.decorator_plain(OwnClass.get_num)
        test_obj = OwnClass(3)
        obj_before_4 = test_obj.get_num(4)
        obj_before_5 = test_obj.get_num(5, extended=True)
        PersistentObjectStorage().dump()
        PersistentObjectStorage().mode = StorageMode.read
        obj_after_4 = test_obj.get_num(4)
        obj_after_4_meta = DataMiner().metadata
        obj_after_5 = test_obj.get_num(5, extended=True)
        obj_after_5_meta = DataMiner().metadata
        self.assertEqual(obj_before_4, obj_after_4)
        self.assertIsInstance(obj_after_4, int)
        self.assertRegex(
            obj_after_4_meta[DataMiner().METADATA_ARG_DEBUG_KEY], "get_num(.*, 4)"
        )
        self.assertEqual(obj_before_5, obj_after_5)
        self.assertIsInstance(obj_after_5, str)
        self.assertRegex(
            obj_after_5_meta[DataMiner().METADATA_ARG_DEBUG_KEY],
            "get_num(.*, 5, extended=True)",
        )

    def testCallNoDebug(self):
        DataMiner().store_arg_debug_metadata = False
        OwnClass.get_num = ObjectStorage.decorator_plain(OwnClass.get_num)
        test_obj = OwnClass(3)
        obj_before_4 = test_obj.get_num(4)
        PersistentObjectStorage().dump()
        PersistentObjectStorage().mode = StorageMode.read
        obj_after_4 = test_obj.get_num(4)
        obj_after_4_meta = DataMiner().metadata
        self.assertEqual(obj_before_4, obj_after_4)
        self.assertIsInstance(obj_after_4, int)
        self.assertEqual(obj_after_4_meta.get(DataMiner().METADATA_ARG_DEBUG_KEY), None)

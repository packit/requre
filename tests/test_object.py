from requre.objects import ObjectStorage
from requre.storage import PersistentObjectStorage
from tests.testbase import BaseClass


class OwnClass:
    def __init__(self, num):
        self.num = num


class StoreAnyRequest(BaseClass):
    domain = "https://example.com/"

    def setUp(self) -> None:
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()


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
        PersistentObjectStorage()._is_write_mode = False
        obj_after = ObjectStorage.execute_all_keys(OwnClass, 1)
        self.assertEqual(obj_before.num, obj_after.num)
        # all objects are already read, next have to fail
        self.assertRaises(
            Exception,
            ObjectStorage.execute_all_keys,
            OwnClass,
            1,
        )

    def testFunctionDecorator(self):
        """
        Test main purpose of the class, decorate class and use it then
        """
        decorated_own = ObjectStorage.decorator_all_keys(OwnClass)
        obj_before = decorated_own(1)
        PersistentObjectStorage().dump()
        PersistentObjectStorage()._is_write_mode = False
        obj_after = decorated_own(1)
        self.assertEqual(obj_before.num, obj_after.num)
        # all objects are already read, next have to fail
        self.assertRaises(Exception, decorated_own, 1)

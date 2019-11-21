import importlib

from requre.helpers.requests_response import RequestResponseHandling
from requre.storage import PersistentObjectStorage
from requre.utils import StorageMode
from tests.testbase import BaseClass


class StoreAnyRequest(BaseClass):
    domain = "https://example.com/"

    def setUp(self) -> None:
        super().setUp()
        self.requests = importlib.import_module("requests")
        self.post_orig = getattr(self.requests, "post")

    def tearDown(self) -> None:
        super().tearDown()
        setattr(self.requests, "post", self.post_orig)

    def testRawCall(self):
        """
        Test if is class is able to explicitly write and read request handling
        """
        keys = [self.domain]
        sess = RequestResponseHandling(store_keys=keys)
        response = self.requests.post(*keys)
        sess.write(response)

        response_after = sess.read()
        self.assertIsInstance(response_after, self.requests.models.Response)
        self.assertNotIn("Example Domain", str(sess.persistent_storage.storage_object))
        self.assertIn("Example Domain", response_after.text)

    def testExecuteWrapper(self):
        """
        test if it is able to use explicit decorator_all_keys for storing request handling
        :return:
        """
        response_before = RequestResponseHandling.execute_all_keys(
            self.requests.post, self.domain
        )
        PersistentObjectStorage().dump()
        PersistentObjectStorage().mode = StorageMode.read
        response_after = RequestResponseHandling.execute_all_keys(
            self.requests.post, self.domain
        )
        self.assertEqual(response_before.text, response_after.text)
        self.assertRaises(
            Exception,
            RequestResponseHandling.execute_all_keys,
            self.requests.post,
            self.domain,
        )

    def testFunctionDecorator(self):
        """
        Test main purpose of the class, decorate post function and use it then
        """
        self.requests.post = RequestResponseHandling.decorator_all_keys(
            self.requests.post
        )
        response_before = self.requests.post(self.domain)
        PersistentObjectStorage().dump()
        PersistentObjectStorage().mode = StorageMode.read

        response_after = self.requests.post(self.domain)
        self.assertEqual(response_before.text, response_after.text)
        self.assertRaises(Exception, self.requests.post, self.domain)

    def testFunctionDecoratorNotFound(self):
        """
        Check if it fails with Exception in case request is not stored
        """
        self.requests.post = RequestResponseHandling.decorator_all_keys(
            self.requests.post
        )
        PersistentObjectStorage().dump()
        PersistentObjectStorage().mode = StorageMode.read
        self.assertRaises(Exception, self.requests.post, self.domain, data={"a": "b"})

    def testFunctionCustomFields(self):
        """
        Test if it is able to use partial storing of args, kwargs
        prepare to avoid leak authentication to data
        """
        self.requests.post = RequestResponseHandling.decorator(item_list=[0])(
            self.requests.post
        )
        response_before = self.requests.post(self.domain)
        response_google_before = self.requests.post(
            "http://www.google.com", data={"a": "b"}
        )
        PersistentObjectStorage().dump()
        PersistentObjectStorage().mode = StorageMode.read

        response_after = self.requests.post(self.domain)
        response_google_after = self.requests.post("http://www.google.com")
        self.assertEqual(response_before.text, response_after.text)
        self.assertEqual(response_google_before.text, response_google_after.text)
        self.assertRaises(Exception, self.requests.post, self.domain)

    def testFunctionCustomFieldsWrong(self):
        """
        Check exceptions if using partial keys storing
        """
        self.requests.post = RequestResponseHandling.decorator(item_list=[0, "data"])(
            self.requests.post
        )
        self.requests.post(self.domain, data={"a": "b"})
        response_2 = self.requests.post(self.domain, data={"c": "d"})
        PersistentObjectStorage().dump()
        PersistentObjectStorage().mode = StorageMode.read

        self.assertRaises(Exception, self.requests.post, self.domain, data={"x": "y"})
        self.assertRaises(KeyError, self.requests.post, self.domain)
        response_2_after = self.requests.post(self.domain, data={"c": "d"})
        self.assertEqual(response_2.text, response_2_after.text)

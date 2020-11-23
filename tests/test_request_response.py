import importlib
import unittest

from requre.exceptions import ItemNotInStorage
from requre.helpers.requests_response import (
    RequestResponseHandling,
    remove_password_from_url,
)
from requre.utils import StorageMode
from tests.testbase import BaseClass, network_connection_available


class StoreAnyRequest(BaseClass):
    domain = "https://example.com/"

    def setUp(self) -> None:
        super().setUp()
        self.requests = importlib.import_module("requests")
        self.post_orig = getattr(self.requests, "post")

    def tearDown(self) -> None:
        super().tearDown()
        setattr(self.requests, "post", self.post_orig)

    @unittest.skipIf(not network_connection_available(), "No network connection")
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
        self.assertNotIn("Example Domain", str(sess.get_cassette().storage_object))
        self.assertIn("Example Domain", response_after.text)

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testExecuteWrapper(self):
        """
        test if it is able to use explicit decorator_all_keys for storing request handling
        :return:
        """
        response_before = RequestResponseHandling.execute_all_keys(
            self.requests.post, self.domain, cassette=self.cassette
        )
        self.cassette.dump()
        self.cassette.mode = StorageMode.read
        response_after = RequestResponseHandling.execute_all_keys(
            self.requests.post, self.domain, cassette=self.cassette
        )
        self.assertEqual(response_before.text, response_after.text)
        self.assertRaises(
            Exception,
            RequestResponseHandling.execute_all_keys,
            self.requests.post,
            self.domain,
            cassette=self.cassette,
        )

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionDecorator(self):
        """
        Test main purpose of the class, decorate post function and use it then
        """
        self.requests.post = RequestResponseHandling.decorator_all_keys()(
            self.requests.post
        )
        response_before = self.requests.post(self.domain)
        self.cassette.dump()
        self.cassette.mode = StorageMode.read

        response_after = self.requests.post(self.domain)
        self.assertEqual(response_before.text, response_after.text)
        self.assertRaises(Exception, self.requests.post, self.domain)

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionDecoratorNotFound(self):
        """
        Check if it fails with Exception in case request is not stored
        """
        self.requests.post = RequestResponseHandling.decorator_all_keys()(
            self.requests.post
        )
        self.cassette.dump()
        self.cassette.mode = StorageMode.read
        self.assertRaises(Exception, self.requests.post, self.domain, data={"a": "b"})

    @unittest.skipIf(not network_connection_available(), "No network connection")
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
        self.cassette.dump()
        self.cassette.mode = StorageMode.read

        response_after = self.requests.post(self.domain)
        response_google_after = self.requests.post("http://www.google.com")
        self.assertEqual(response_before.text, response_after.text)
        self.assertEqual(response_google_before.text, response_google_after.text)
        self.assertRaises(Exception, self.requests.post, self.domain)

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionCustomFieldsWrong(self):
        """
        Check exceptions if using partial keys storing
        """
        self.requests.post = RequestResponseHandling.decorator(item_list=[0, "data"])(
            self.requests.post
        )
        self.requests.post(self.domain, data={"a": "b"})
        response_2 = self.requests.post(self.domain, data={"c": "d"})
        self.cassette.dump()
        self.cassette.mode = StorageMode.read

        self.assertRaises(Exception, self.requests.post, self.domain, data={"x": "y"})
        self.assertRaises(ItemNotInStorage, self.requests.post, self.domain)
        response_2_after = self.requests.post(self.domain, data={"c": "d"})
        self.assertEqual(response_2.text, response_2_after.text)

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionCustomFieldsCheckKeys(self):
        self.requests.post = RequestResponseHandling.decorator(
            item_list=["url", "data"], map_function_to_item={"url": lambda x: x[0:10]}
        )(self.requests.post)
        self.requests.post(self.domain)
        self.requests.post("http://www.google.com", data={"a": "b"})
        self.cassette.dump()
        self.cassette.mode = StorageMode.read
        print(">>>", self.cassette.storage_object)
        self.assertIn(
            "https://ex",
            self.cassette.storage_object["unittest.case"][
                "tests.test_request_response"
            ]["requre.objects"]["requre.cassette"]["requests.api"]["post"],
        )
        self.assertIn(
            "http://www",
            self.cassette.storage_object["unittest.case"][
                "tests.test_request_response"
            ]["requre.objects"]["requre.cassette"]["requests.api"]["post"],
        )

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionFilterHeaders(self):
        self.requests.post = RequestResponseHandling.decorator(
            item_list=["url"],
            response_headers_to_drop=["Date"],
        )(self.requests.post)
        self.requests.post(self.domain)
        self.requests.post("http://www.google.com", data={"a": "b"})
        self.cassette.dump()
        self.cassette.mode = StorageMode.read

        saved_item = self.cassette.storage_object["unittest.case"][
            "tests.test_request_response"
        ]["requre.objects"]["requre.cassette"]["requests.api"]["post"][
            "http://www.google.com"
        ][
            0
        ]

        self.assertIn("headers", saved_item["output"])
        self.assertIsNone(saved_item["output"]["headers"]["Date"])

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionFilterUnknownHeaders(self):
        self.requests.post = RequestResponseHandling.decorator(
            item_list=["url"],
            response_headers_to_drop=["NotKnownHeader"],
        )(self.requests.post)
        self.requests.post(self.domain)
        self.requests.post("http://www.google.com", data={"a": "b"})
        self.cassette.dump()
        self.cassette.mode = StorageMode.read

        saved_item = self.cassette.storage_object["unittest.case"][
            "tests.test_request_response"
        ]["requre.objects"]["requre.cassette"]["requests.api"]["post"][
            "http://www.google.com"
        ][
            0
        ]

        self.assertIn("headers", saved_item["output"])
        self.assertNotIn("NotKnownHeader", saved_item["output"]["headers"])

    def testUrlCleanup(self):
        self.assertEqual(
            remove_password_from_url("http://user:pass@www.google.com/"),
            "http://user:???@www.google.com/",
        )
        self.assertEqual(
            remove_password_from_url("http://www.google.com/"), "http://www.google.com/"
        )
        self.assertIn(
            "/a/b/asdsa?x&y=y#z",
            remove_password_from_url(
                "http://user:pass@www.google.com/a/b/asdsa?x&y=y#z"
            ),
        )

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import importlib
import unittest

from requre.exceptions import ItemNotInStorage
from requre.helpers.httpx_response import HTTPXRequestResponseHandling
from requre.utils import StorageMode
from tests.testbase import BaseClass, network_connection_available


class StoreAnyRequest(BaseClass):
    domain = "https://example.com/"

    def setUp(self) -> None:
        super().setUp()
        self.httpx = importlib.import_module("httpx")
        self.post_orig = getattr(self.httpx, "post")

    def tearDown(self) -> None:
        super().tearDown()
        setattr(self.httpx, "post", self.post_orig)

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testRawCall(self):
        """
        Test if is class is able to explicitly write and read request handling
        """
        # example.com domain is not accepting POST requests anymore
        # using stg.packit.dev instead
        keys = [
            "https://stg.packit.dev/api/webhooks/github",
        ]
        sess = HTTPXRequestResponseHandling(store_keys=keys)
        response = self.httpx.post(*keys)
        sess.write(response)

        response_after = sess.read()
        self.assertIsInstance(response_after, self.httpx.Response)
        message = (
            "Did not attempt to load JSON data because the request "
            "Content-Type was not 'application/json'."
        )
        self.assertNotIn(message, str(sess.get_cassette().storage_object))
        self.assertIn(message, response_after.text)

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testExecuteWrapper(self):
        """
        test if it is able to use explicit decorator_all_keys for storing request handling
        :return:
        """
        response_before = HTTPXRequestResponseHandling.execute_all_keys(
            self.httpx.post, self.domain, cassette=self.cassette
        )
        self.cassette.dump()
        self.cassette.mode = StorageMode.read
        response_after = HTTPXRequestResponseHandling.execute_all_keys(
            self.httpx.post, self.domain, cassette=self.cassette
        )
        self.assertEqual(response_before.text, response_after.text)
        self.assertRaises(
            Exception,
            HTTPXRequestResponseHandling.execute_all_keys,
            self.httpx.post,
            self.domain,
            cassette=self.cassette,
        )

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionDecorator(self):
        """
        Test main purpose of the class, decorate post function and use it then
        """
        self.httpx.post = HTTPXRequestResponseHandling.decorator_all_keys()(
            self.httpx.post
        )
        response_before = self.httpx.post(self.domain)
        self.cassette.dump()
        self.cassette.mode = StorageMode.read

        response_after = self.httpx.post(self.domain)
        self.assertEqual(response_before.text, response_after.text)
        self.assertRaises(Exception, self.httpx.post, self.domain)

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionDecoratorNotFound(self):
        """
        Check if it fails with Exception in case request is not stored
        """
        self.httpx.post = HTTPXRequestResponseHandling.decorator_all_keys()(
            self.httpx.post
        )
        self.cassette.dump()
        self.cassette.mode = StorageMode.read
        self.assertRaises(Exception, self.httpx.post, self.domain, data={"a": "b"})

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionCustomFields(self):
        """
        Test if it is able to use partial storing of args, kwargs
        prepare to avoid leak authentication to data
        """
        self.httpx.post = HTTPXRequestResponseHandling.decorator(item_list=[0])(
            self.httpx.post
        )
        response_before = self.httpx.post(self.domain)
        response_google_before = self.httpx.post(
            "http://www.google.com", data={"a": "b"}
        )
        self.cassette.dump()
        self.cassette.mode = StorageMode.read

        response_after = self.httpx.post(self.domain)
        response_google_after = self.httpx.post("http://www.google.com")
        self.assertEqual(response_before.text, response_after.text)
        self.assertEqual(response_google_before.text, response_google_after.text)
        self.assertRaises(Exception, self.httpx.post, self.domain)

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionCustomFieldsWrong(self):
        """
        Check exceptions if using partial keys storing
        """
        self.httpx.post = HTTPXRequestResponseHandling.decorator(
            item_list=["url", "data"]
        )(self.httpx.post)
        self.httpx.post(self.domain, data={"a": "b"})
        response_2 = self.httpx.post(self.domain, data={"c": "d"})
        self.cassette.dump()
        self.cassette.mode = StorageMode.read

        self.assertRaises(Exception, self.httpx.post, self.domain, data={"x": "y"})
        self.assertRaises(ItemNotInStorage, self.httpx.post, self.domain)
        response_2_after = self.httpx.post(self.domain, data={"c": "d"})
        self.assertEqual(response_2.text, response_2_after.text)

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionCustomFieldsCheckKeys(self):
        self.httpx.post = HTTPXRequestResponseHandling.decorator(
            item_list=["url"], map_function_to_item={"url": lambda x: x[0:10]}
        )(self.httpx.post)
        self.httpx.post(self.domain)
        self.httpx.post("http://www.google.com", data={"a": "b"})
        self.cassette.dump()
        self.cassette.mode = StorageMode.read
        print(">>>", self.cassette.storage_object)
        self.assertIn(
            "https://ex",
            self.cassette.storage_object["unittest.case"]["tests.test_httpx"][
                "requre.objects"
            ]["requre.cassette"]["httpx"]["post"],
        )
        self.assertIn(
            "http://www",
            self.cassette.storage_object["unittest.case"]["tests.test_httpx"][
                "requre.objects"
            ]["requre.cassette"]["httpx"]["post"],
        )

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionFilterHeaders(self):
        self.httpx.post = HTTPXRequestResponseHandling.decorator(
            item_list=["url"],
            response_headers_to_drop=["date"],
        )(self.httpx.post)
        self.httpx.post(self.domain)
        self.httpx.post("http://www.google.com", data={"a": "b"})
        self.cassette.dump()
        self.cassette.mode = StorageMode.read

        saved_item = self.cassette.storage_object["unittest.case"]["tests.test_httpx"][
            "requre.objects"
        ]["requre.cassette"]["httpx"]["post"]["http://www.google.com"][0]

        self.assertIn("headers", saved_item["output"])
        self.assertIsNone(saved_item["output"]["headers"]["date"])

    @unittest.skipIf(not network_connection_available(), "No network connection")
    def testFunctionFilterUnknownHeaders(self):
        self.httpx.post = HTTPXRequestResponseHandling.decorator(
            item_list=["url"],
            response_headers_to_drop=["NotKnownHeader"],
        )(self.httpx.post)
        self.httpx.post(self.domain)
        self.httpx.post("http://www.google.com", data={"a": "b"})
        self.cassette.dump()
        self.cassette.mode = StorageMode.read

        saved_item = self.cassette.storage_object["unittest.case"]["tests.test_httpx"][
            "requre.objects"
        ]["requre.cassette"]["httpx"]["post"]["http://www.google.com"][0]

        self.assertIn("headers", saved_item["output"])
        self.assertNotIn("NotKnownHeader", saved_item["output"]["headers"])

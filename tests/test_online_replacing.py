import math
import os
import socket
import unittest

import requests

import tests.data.special_requre_module
from requre.cassette import Cassette, StorageMode
from requre.helpers.requests_response import RequestResponseHandling
from requre.helpers.simple_object import Simple
from requre.online_replacing import (
    replace_module_match,
    apply_decorator_to_all_methods,
    record_requests_for_all_methods,
)
from tests.data import special_requre_module
from tests.data.special_requre_module import hello


def guard(*args, **kwargs):
    raise IOError("No Internet connection")


original_socket = socket.socket

SELECTOR = str(os.path.basename(__file__).rsplit(".", 1)[0])
TEST_DIR = os.path.dirname(__file__)


def decorator_exact(func):
    def _int():
        return "decorator_c " + func()

    return _int


def decorator_inc(func):
    def _int_inc(a):
        return func(a) + 1

    return _int_inc


@replace_module_match(
    what="tests.data.special_requre_module.hello", decorate=decorator_exact
)
def decorated_exact():
    return tests.data.special_requre_module.hello() + hello() + "exact"


class TestOnlinePatchingModuleMatch(unittest.TestCase):
    def testDecoratorImport(self):
        self.assertEqual(decorated_exact(), "decorator_c Hi! decorator_c Hi! exact")
        # test reverting one decorators
        self.assertEqual(tests.data.special_requre_module.hello(), "Hi! ")
        self.assertEqual(hello(), "Hi! ")

    @replace_module_match(
        what="tests.data.special_requre_module.hello", decorate=decorator_exact
    )
    def testDecoratorMainUsage(self):
        self.assertEqual(tests.data.special_requre_module.hello(), "decorator_c Hi! ")
        self.assertEqual(hello(), "decorator_c Hi! ")
        self.assertEqual(special_requre_module.hello(), "decorator_c Hi! ")

    @replace_module_match(
        what="tests.data.special_requre_module.hello",
        decorate=[decorator_exact, decorator_exact],
    )
    @replace_module_match(
        what="tests.data.special_requre_module.inc", decorate=decorator_inc
    )
    def testDecoratorMultipleDecorators(self):
        self.assertEqual(hello(), "decorator_c decorator_c Hi! ")
        # verify the decorator
        self.assertEqual(decorator_inc(lambda x: x)(1), 2)
        # verify decorated function
        self.assertEqual(tests.data.special_requre_module.inc(1), 3)


# part of documented workaround for the next testcase
setattr(tests.data.special_requre_module.dynamic, "other", lambda self: "static")


class DynamicMethods(unittest.TestCase):
    @replace_module_match(
        what="tests.data.special_requre_module.dynamic.some", decorate=decorator_exact
    )
    def testDynamicClassMethodNotWorking(self):
        self.assertRaises(
            AttributeError, getattr, tests.data.special_requre_module.dynamic, "some"
        )
        self.assertEqual(tests.data.special_requre_module.dynamic().some(), "SOME")

    @unittest.skip("this also does not work, probably caused by pytest execution")
    @replace_module_match(
        what="tests.data.special_requre_module.dynamic.other", decorate=decorator_exact
    )
    def testDynamicClassMethodWorking(self):
        self.assertEqual(
            tests.data.special_requre_module.dynamic().other(), "decorated_c static"
        )


class CassetteSelection(unittest.TestCase):
    def setUp(self) -> None:
        # disable internet access via sockets
        setattr(socket, "socket", guard)

    def reset(self):
        setattr(socket, "socket", original_socket)

    def tearDown(self) -> None:
        self.reset()

    def testGuard(self):
        # check if
        self.assertRaises(IOError, requests.get, "http://example.com")

    @replace_module_match(
        what="requests.sessions.Session.request",
        decorate=RequestResponseHandling.decorator(item_list=["method", "url"]),
    )
    def testWrite(self, cassette: Cassette):
        self.reset()
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)
        self.assertFalse(os.path.exists(cassette.storage_file))
        cassette.dump()
        self.assertTrue(os.path.exists(cassette.storage_file))
        os.remove(cassette.storage_file)

    @replace_module_match(
        what="requests.sessions.Session.request",
        decorate=RequestResponseHandling.decorator(item_list=["method", "url"]),
    )
    def testRead(self, cassette: Cassette):
        if cassette.mode == StorageMode.read:
            self.assertTrue(os.path.exists(cassette.storage_file))
        else:
            self.reset()
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)

    @replace_module_match(
        what="requests.sessions.Session.request",
        decorate=RequestResponseHandling.decorator(item_list=["method", "url"]),
    )
    @replace_module_match(what="math.sin", decorate=Simple.decorator(item_list=[]))
    def testReadMultiple(self, cassette: Cassette):
        assert cassette
        if cassette.mode == StorageMode.write:
            self.reset()
            sin_output = math.sin(1.5)
        else:
            sin_output = math.sin(4)
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)
        self.assertAlmostEqual(0.9974949866040544, sin_output, delta=0.0005)


new_cassette = Cassette()


@apply_decorator_to_all_methods(
    replace_module_match(
        what="math.sin", decorate=Simple.decorator_plain(), cassette=new_cassette
    )
)
@record_requests_for_all_methods(cassette=new_cassette)
class DecoratorClassApply(unittest.TestCase):
    # when regeneration, comment lines with assert equals, because checks for eqality does not work
    def setUp(self):
        new_cassette.storage_file = None

    def test0(self, cassette: Cassette):
        if cassette.mode == StorageMode.read:
            self.assertEqual(len(new_cassette.storage_object["math"]["sin"]), 1)
        sin_output = math.sin(1.5)
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)
        self.assertAlmostEqual(0.9974949866040544, sin_output, delta=0.0005)

    def test1(self):
        sin_output = math.sin(1.5)
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)
        self.assertAlmostEqual(0.9974949866040544, sin_output, delta=0.0005)

    def test2(self, cassette: Cassette):
        if cassette.mode == StorageMode.read:
            self.assertEqual(len(new_cassette.storage_object["math"]["sin"]), 2)
        self.test1()
        if cassette.mode == StorageMode.read:
            self.assertEqual(len(new_cassette.storage_object["math"]["sin"]), 1)

import socket
import os
import unittest
import requests
import math

import tests.data.special_requre_module
from requre.online_replacing import replace, replace_module_match
from requre.cassette import Cassette
from requre.storage import PersistentObjectStorage
from requre.helpers.requests_response import RequestResponseHandling
from requre.helpers.simple_object import Simple
from tests.data import special_requre_module
from tests.data.special_requre_module import hello


def guard(*args, **kwargs):
    raise IOError("No Internet connection")


original_socket = socket.socket

SELECTOR = str(os.path.basename(__file__).rsplit(".", 1)[0])
TEST_DIR = os.path.dirname(__file__)


def decorator_a(func):
    def _int():
        return "decorator_a " + func()

    return _int


def decorator_b(func):
    def _int():
        return "decorator_b " + func()

    return _int


@replace(in_module=SELECTOR, what="hello", decorate=decorator_a)
def decorated_int():
    return hello() + "outer"


@replace(in_module="special_requre_module", what="hello", decorate=decorator_b)
def decorated_ext():
    return tests.data.special_requre_module.hello() + "outer"


class TestOnlinePatchingDecorate(unittest.TestCase):
    def testDecoratorImport(self):
        self.assertEqual(decorated_ext(), "decorator_b Hi! outer")
        # test revenrting
        self.assertEqual(tests.data.special_requre_module.hello(), "Hi! ")

    def testDecoratorFrom(self):
        self.assertEqual(decorated_int(), "decorator_a Hi! outer")
        self.assertEqual(hello(), "Hi! ")

    @replace(in_module="special_requre_module", what="hello", decorate=decorator_b)
    def testDecoratorMainUsage(self):
        self.assertEqual(tests.data.special_requre_module.hello(), "decorator_b Hi! ")

    # @replace(in_module="special_requre_module", what="hello", decorate=decorator_a)
    # @replace(in_module="special_requre_module", what="hello", decorate=decorator_b)
    def XtestDecoratorMoreDecorators(self):
        print("\n", tests.data.special_requre_module.hello())
        self.assertEqual(
            tests.data.special_requre_module.hello(), "decorator_a decorator_b Hi! "
        )


class TestOnlinePatchingReplace(unittest.TestCase):
    @replace(
        in_module="special_requre_module", what="hello", replace=lambda: "replaced HI"
    )
    def test(self):
        self.assertEqual(tests.data.special_requre_module.hello(), "replaced HI")


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
        # test revenrting
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


own_cassette = Cassette()


class CassetteSelection(unittest.TestCase):
    def setUp(self) -> None:
        # disable internet access via sockets
        setattr(socket, "socket", guard)
        own_cassette.storage_file = None

    def reset(self):
        setattr(socket, "socket", original_socket)

    def tearDown(self) -> None:
        self.reset()

    def testGuard(self):
        # check if
        self.assertRaises(IOError, requests.get, "http://example.com")

    @replace_module_match(
        cassette=own_cassette,
        what="requests.sessions.Session.request",
        decorate=RequestResponseHandling.decorator(item_list=["method", "url"]),
    )
    def testWrite(self):
        self.reset()
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)
        self.assertFalse(os.path.exists(own_cassette.storage_file))
        own_cassette.dump()
        self.assertTrue(os.path.exists(own_cassette.storage_file))
        os.remove(own_cassette.storage_file)

    @replace_module_match(
        cassette=own_cassette,
        what="requests.sessions.Session.request",
        decorate=RequestResponseHandling.decorator(item_list=["method", "url"]),
    )
    def testRead(self):
        # uncomment it and remove storage file to regenerate data
        # self.reset()
        self.assertTrue(os.path.exists(own_cassette.storage_file))
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)

    @replace_module_match(
        what="requests.sessions.Session.request",
        decorate=RequestResponseHandling.decorator(item_list=["method", "url"]),
    )
    def testReadDefaultCassette(self):
        # uncomment it and remove storage file to regenerate data
        # self.reset()
        self.assertEqual(own_cassette.storage_file, None)
        self.assertNotIn(
            self.__class__.__name__,
            PersistentObjectStorage().cassette.storage_file or "",
        )
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)

    @replace_module_match(
        cassette=own_cassette,
        what="requests.sessions.Session.request",
        decorate=RequestResponseHandling.decorator(item_list=["method", "url"]),
    )
    @replace_module_match(what="math.sin", decorate=Simple.decorator(item_list=[]))
    def testReadMultiple(self):
        # uncomment it and remove storage file to regenerate data
        # self.reset()
        # sin_output = math.sin(1.5)
        # comment out this line for regeneration (output is another than this number)
        sin_output = math.sin(4)
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)
        self.assertAlmostEqual(0.9974949866040544, sin_output, delta=0.0005)

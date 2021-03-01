import unittest
import math
import os
from requre.objects import ObjectStorage
from requre.utils import StorageMode
from requre.helpers.guess_object import Guess, GUESS_STR
from requre.helpers.simple_object import Void, Simple
from requre.online_replacing import apply_decorator_to_all_methods, replace_module_match
from requre.cassette import Cassette
from tests.testbase import BaseClass
from tests.test_object import OwnClass
import sys


class Unit(BaseClass):
    def testVoid(self):
        self.assertEqual(Void, Guess.guess_type(sys.__stdout__))

    def testSimple(self):
        self.assertEqual(Simple, Guess.guess_type("abc"))
        self.assertEqual(Simple, Guess.guess_type({1: 2, "a": "b"}))
        self.assertNotEqual(ObjectStorage, Guess.guess_type({1: 2, "a": "b"}))

    def testPickle(self):
        self.assertEqual(ObjectStorage, Guess.guess_type(OwnClass(1)))
        self.assertNotEqual(Void, Guess.guess_type(OwnClass(1)))
        self.assertNotEqual(Simple, Guess.guess_type(OwnClass(1)))


def obj_return(num, obj):
    _ = num
    return obj


class Store(BaseClass):
    def testFunctionDecorator(self):
        """
        Check if it is able to guess and store/restore proper values with types
        """
        decorated_own = Guess.decorator(cassette=self.cassette, item_list=[0])(
            obj_return
        )
        before1 = decorated_own(1, "abc")
        before2 = decorated_own(2, OwnClass(2))
        before3 = decorated_own(2, OwnClass(3))
        before4 = decorated_own(3, sys.__stdin__)
        before5 = decorated_own(
            4,
            (
                1,
                2,
            ),
        )
        self.cassette.dump()
        self.cassette.mode = StorageMode.read

        after2 = decorated_own(2, OwnClass(2))
        self.assertEqual(
            self.cassette.data_miner.metadata[GUESS_STR], ObjectStorage.__name__
        )
        after3 = decorated_own(2, OwnClass(3))
        self.assertEqual(
            self.cassette.data_miner.metadata[GUESS_STR], ObjectStorage.__name__
        )
        after1 = decorated_own(1, "abc")
        self.assertEqual(self.cassette.data_miner.metadata[GUESS_STR], Simple.__name__)
        after4 = decorated_own(3, sys.__stdin__)
        self.assertEqual(self.cassette.data_miner.metadata[GUESS_STR], Void.__name__)
        after5 = decorated_own(4, (3,))
        self.assertEqual(
            after5,
            (
                1,
                2,
            ),
        )
        self.assertTrue(isinstance(after5, tuple))

        self.assertEqual(before1, after1)
        self.assertEqual(before2.__class__.__name__, after2.__class__.__name__)
        self.assertEqual(before3.__class__.__name__, after3.__class__.__name__)
        self.assertEqual(after2.__class__.__name__, "OwnClass")
        self.assertEqual(before4.__class__.__name__, "TextIOWrapper")
        self.assertEqual(after4.__class__.__name__, "str")
        self.assertEqual(before5.__class__.__name__, "tuple")
        self.assertEqual(before5, after5)


@apply_decorator_to_all_methods(replace_module_match(what="math.sin"))
class ApplyDefaultDecorator(unittest.TestCase):
    SIN_OUTPUT = 0.9974949866040544

    def cassette_setup(self, cassette):
        self.assertEqual(cassette.storage_object, {})

    def cassette_teardown(self, cassette):
        os.remove(cassette.storage_file)

    def test(self, cassette: Cassette):
        math.sin(1.5)
        self.assertEqual(len(cassette.storage_object["math"]["sin"]), 1)
        self.assertAlmostEqual(
            self.SIN_OUTPUT,
            cassette.storage_object["math"]["sin"][0]["output"],
            delta=0.0005,
        )
        self.assertEqual(
            cassette.storage_object["math"]["sin"][0]["metadata"][GUESS_STR],
            "Simple",
        )

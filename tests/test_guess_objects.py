from requre.objects import ObjectStorage
from requre.utils import StorageMode
from requre.helpers.guess_object import Guess, GUESS_STR
from requre.helpers.simple_object import Void, Simple
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
        self.cassette.dump()
        self.cassette.mode = StorageMode.read
        print(self.cassette.storage_object)

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

        self.assertEqual(before1, after1)
        self.assertEqual(before2.__class__.__name__, after2.__class__.__name__)
        self.assertEqual(before3.__class__.__name__, after3.__class__.__name__)
        self.assertEqual(after2.__class__.__name__, "OwnClass")
        self.assertEqual(before4.__class__.__name__, "TextIOWrapper")
        self.assertEqual(after4.__class__.__name__, "str")

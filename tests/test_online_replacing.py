import os
import unittest

import tests.data.special_requre_module
from requre.online_replacing import replace, replace_module_match
from requre.storage import PersistentObjectStorage, DataMiner, StorageKeysInspectFull
from tests.data import special_requre_module
from tests.data.special_requre_module import hello

SELECTOR = str(os.path.basename(__file__).rsplit(".", 1)[0])


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
        # check if  there is is full inspect stragegy
        self.assertEqual(DataMiner().key_stategy_cls, StorageKeysInspectFull)
        self.assertEqual(decorated_exact(), "decorator_c Hi! decorator_c Hi! exact")
        # check if inspect stragety it reverted back (internally used Simple)
        self.assertEqual(DataMiner().key_stategy_cls, StorageKeysInspectFull)
        # check if storage file is set properly
        self.assertIn(
            "requre/tests/test_data/test_online_replacing/decorated_exact.yaml",
            str(PersistentObjectStorage().storage_file),
        )
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
        # check also if proper filename is used for Persistent Storage
        self.assertIn(
            "requre/tests/test_data/test_online_replacing/"
            "tests.test_online_replacing."
            "TestOnlinePatchingModuleMatch.testDecoratorMainUsage.yaml",
            str(PersistentObjectStorage().storage_file),
        )

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

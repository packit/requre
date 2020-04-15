import unittest
import os
from requre.online_replacing import replace
import tests.data.special_requre_module
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
        self.assertEqual(tests.data.special_requre_module.hello(), "decorator_a decorator_b Hi! ")


class TestOnlinePatchingReplace(unittest.TestCase):

    @replace(in_module="special_requre_module", what="hello", replace=lambda: "replaced HI")
    def test(self):
        self.assertEqual(tests.data.special_requre_module.hello(), "replaced HI")

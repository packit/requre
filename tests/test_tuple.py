import sys
import tempfile
from requre.helpers.simple_object import Tuple
from requre.online_replacing import apply_decorator_to_all_methods, replace
from requre.cassette import Cassette, StorageMode
from tests.testbase import BaseClass, RetTuple


@apply_decorator_to_all_methods(
    replace(what="tests.testbase.RetTuple.ret", decorate=Tuple.decorator_plain())
)
class TestTuple(BaseClass):
    def test_write(self, cassette: Cassette):
        cassette.storage_file = tempfile.mktemp()
        out = RetTuple().ret(1)
        self.assertEqual(out, ("ret", 1))

    def test_read(self, cassette: Cassette):
        print(cassette.storage_file)
        print([k for k, v in sys.modules.items() if "tests" in k])
        if cassette.mode == StorageMode.write:
            out = RetTuple().ret(2)
            self.assertEqual(out, ("ret", 2))
        else:
            out = RetTuple().ret(1)
            self.assertEqual(out, ("ret", 2))

import builtins
import os
import sys
import unittest

import requre
from requre.utils import STORAGE
from requre.helpers.tempfile import TempFile
from requre.import_system import (
    ReplaceType,
    _upgrade_import_system,
    upgrade_import_system,
)

SELECTOR = os.path.basename(__file__).rsplit(".", 1)[0]


class TestUpgradeImportSystem(unittest.TestCase):
    def setUp(self) -> None:
        requre.import_system.replace_dict = {}

    def tearDown(self) -> None:
        if "tempfile" in sys.modules:
            del sys.modules["tempfile"]
        super().tearDown()

    def testImport(self):
        """
        Test improving of import system with import statement
        Check also debug file output if it contains proper debug data
        """
        debug_file = "__modules.log"
        HANDLE_MODULE_LIST = [
            (
                "^tempfile$",
                {"who_name": "test_import_system"},
                {"mktemp": [ReplaceType.REPLACE, lambda: "a"]},
            )
        ]
        builtins.__import__ = _upgrade_import_system(
            builtins.__import__, name_filters=HANDLE_MODULE_LIST, debug_file=debug_file
        )
        import tempfile

        self.assertNotIn("/tmp", tempfile.mktemp())
        self.assertIn("a", tempfile.mktemp())
        with open(debug_file, "r") as fd:
            output = fd.read()
            self.assertIn(SELECTOR, output)
            self.assertIn("replacing mktemp by function", output)
        os.remove(debug_file)

    def testImportFrom(self):
        """
        Test if it able to patch also from statement
        """
        HANDLE_MODULE_LIST = [
            (
                "^tempfile$",
                {"who_name": SELECTOR},
                {"mktemp": [ReplaceType.REPLACE, lambda: "b"]},
            )
        ]
        builtins.__import__ = _upgrade_import_system(
            builtins.__import__, name_filters=HANDLE_MODULE_LIST
        )
        from tempfile import mktemp

        self.assertNotIn("/tmp", mktemp())
        self.assertIn("b", mktemp())

    def testImportDecorator(self):
        """
        Test patching by decorator_all_keys, not replacing whole function
        """
        HANDLE_MODULE_LIST = [
            (
                "^tempfile$",
                {"who_name": SELECTOR},
                {
                    "mktemp": [
                        ReplaceType.DECORATOR,
                        lambda x: lambda: f"decorated {x()}",
                    ]
                },
            )
        ]
        upgrade_import_system(HANDLE_MODULE_LIST)
        import tempfile

        self.assertIn("decorated", tempfile.mktemp())
        self.assertIn("/tmp", tempfile.mktemp())

    def testImportReplaceModule(self):
        """
        Test if it is able to replace whole module by own implemetation
        Test also own implementation of static tempfile module via class
        """

        HANDLE_MODULE_LIST = [
            (
                "^tempfile$",
                {"who_name": SELECTOR},
                {"": [ReplaceType.REPLACE_MODULE, TempFile]},
            )
        ]
        builtins.__import__ = _upgrade_import_system(
            builtins.__import__, name_filters=HANDLE_MODULE_LIST
        )
        import tempfile

        tmpfile = tempfile.mktemp()
        tmpdir = tempfile.mkdtemp()
        self.assertIn(f"/tmp/{os.path.basename(STORAGE.storage_file)}/static_tmp", tmpfile)
        self.assertIn(f"/tmp/{os.path.basename(STORAGE.storage_file)}/static_tmp", tmpdir)
        self.assertFalse(os.path.exists(tmpfile))
        self.assertTrue(os.path.exists(tmpdir))
        self.assertTrue(os.path.isdir(tmpdir))
        os.removedirs(tmpdir)

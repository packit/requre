import builtins
import os
import sys

from requre import decorate, replace, replace_module
from requre.helpers.tempfile import TempFile
from requre.import_system import ReplaceType, upgrade_import_system, UpgradeImportSystem
from requre.storage import PersistentObjectStorage
from tests.testbase import BaseClass

SELECTOR = str(os.path.basename(__file__).rsplit(".", 1)[0])


class TestUpgradeImportSystem(BaseClass):
    def setUp(self) -> None:
        super().setUp()
        self.old_imports = builtins.__import__

    def tearDown(self) -> None:
        builtins.__import__ = self.old_imports
        if "tempfile" in sys.modules:
            del sys.modules["tempfile"]
        super().tearDown()

    def test_no_filter(self):
        old_imports = builtins.__import__
        with UpgradeImportSystem():
            import tempfile

            self.assertNotIn("decorated", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())
        assert builtins.__import__ == old_imports

    def test_import_from(self):
        """
        Test if it is able to patch also from statement
        """
        replace(
            where="^tempfile$",
            what="mktemp",
            replacement=lambda: "b",
            who_name=SELECTOR,
        )
        from tempfile import mktemp

        self.assertNotIn("/tmp", mktemp())
        self.assertIn("b", mktemp())

    def test_filter_replace(self):
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
        upgrade_import_system(filters=HANDLE_MODULE_LIST, debug_file=debug_file)
        import tempfile

        self.assertNotIn("/tmp", tempfile.mktemp())
        self.assertIn("a", tempfile.mktemp())
        with open(debug_file, "r") as fd:
            output = fd.read()
            self.assertIn(SELECTOR, output)
            self.assertIn("replacing mktemp by function", output)
        os.remove(debug_file)

    def test_method_replace(self):
        """
        Test improving of import system with import statement
        Check also debug file output if it contains proper debug data
        """
        debug_file = "__modules.log"
        UpgradeImportSystem(debug_file=debug_file).replace(
            where="^tempfile$",
            what="mktemp",
            replacement=lambda: "a",
            who_name="test_import_system",
        )
        import tempfile

        self.assertNotIn("/tmp", tempfile.mktemp())
        self.assertIn("a", tempfile.mktemp())
        with open(debug_file, "r") as fd:
            output = fd.read()
            self.assertIn(SELECTOR, output)
            self.assertIn("replacing mktemp by function", output)
        os.remove(debug_file)

    def test_method_context_replace(self):
        """
        Test improving of import system with import statement
        Check also debug file output if it contains proper debug data
        """
        debug_file = "__modules.log"
        with UpgradeImportSystem(debug_file=debug_file).replace(
            where="^tempfile$",
            what="mktemp",
            replacement=lambda: "a",
            who_name="test_import_system",
        ):
            import tempfile

            self.assertNotIn("/tmp", tempfile.mktemp())
            self.assertIn("a", tempfile.mktemp())
            with open(debug_file, "r") as fd:
                output = fd.read()
                self.assertIn(SELECTOR, output)
                self.assertIn("replacing mktemp by function", output)
        os.remove(debug_file)

    def test_function_replace(self):
        """
        Test improving of import system with import statement
        Check also debug file output if it contains proper debug data
        """
        debug_file = "__modules.log"
        replace(
            where="^tempfile$",
            what="mktemp",
            replacement=lambda: "a",
            who_name="test_import_system",
            debug_file=debug_file,
        )
        import tempfile

        self.assertNotIn("/tmp", tempfile.mktemp())
        self.assertIn("a", tempfile.mktemp())
        with open(debug_file, "r") as fd:
            output = fd.read()
            self.assertIn(SELECTOR, output)
            self.assertIn("replacing mktemp by function", output)
        os.remove(debug_file)

    def test_function_context_replace(self):
        """
        Test improving of import system with import statement
        Check also debug file output if it contains proper debug data
        """
        debug_file = "__modules.log"
        with replace(
            where="^tempfile$",
            what="mktemp",
            replacement=lambda: "a",
            who_name="test_import_system",
            debug_file=debug_file,
        ):
            import tempfile

            self.assertNotIn("/tmp", tempfile.mktemp())
            self.assertIn("a", tempfile.mktemp())
            with open(debug_file, "r") as fd:
                output = fd.read()
                self.assertIn(SELECTOR, output)
                self.assertIn("replacing mktemp by function", output)
            os.remove(debug_file)

    def test_filter_decorate(self):
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
        upgrade_import_system(filters=HANDLE_MODULE_LIST)
        import tempfile

        self.assertIn("decorated", tempfile.mktemp())
        self.assertIn("/tmp", tempfile.mktemp())

    def test_method_decorate(self):
        """
        Test patching by decorator_all_keys, not replacing whole function
        """
        UpgradeImportSystem().decorate(
            where="^tempfile$",
            what="mktemp",
            decorator=lambda x: lambda: f"decorated {x()}",
            who_name=SELECTOR,
        )

        import tempfile

        self.assertIn("decorated", tempfile.mktemp())
        self.assertIn("/tmp", tempfile.mktemp())

    def test_method_context_decorate(self):
        """
        Test patching by decorator_all_keys, not replacing whole function
        """
        with UpgradeImportSystem().decorate(
            where="^tempfile$",
            what="mktemp",
            decorator=lambda x: lambda: f"decorated {x()}",
            who_name=SELECTOR,
        ):
            import tempfile

            self.assertIn("decorated", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())

    def test_function_decorate(self):
        """
        Test patching by decorator_all_keys, not replacing whole function
        """
        decorate(
            where="^tempfile$",
            what="mktemp",
            decorator=lambda x: lambda: f"decorated {x()}",
            who_name=SELECTOR,
        )

        import tempfile

        self.assertIn("decorated", tempfile.mktemp())
        self.assertIn("/tmp", tempfile.mktemp())

    def test_function_context_decorate(self):
        """
        Test patching by decorator_all_keys, not replacing whole function
        """
        with decorate(
            where="^tempfile$",
            what="mktemp",
            decorator=lambda x: lambda: f"decorated {x()}",
            who_name=SELECTOR,
        ):
            import tempfile

            self.assertIn("decorated", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())

    def test_filter_replace_module(self):
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
        upgrade_import_system(filters=HANDLE_MODULE_LIST)
        import tempfile

        tmpfile = tempfile.mktemp()
        tmpdir = tempfile.mkdtemp()
        self.assertIn(
            f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp",
            tmpfile,
        )
        self.assertIn(
            f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp",
            tmpdir,
        )
        self.assertFalse(os.path.exists(tmpfile))
        self.assertTrue(os.path.exists(tmpdir))
        self.assertTrue(os.path.isdir(tmpdir))
        os.removedirs(tmpdir)

    def test_method_replace_module(self):
        """
        Test if it is able to replace whole module by own implemetation
        Test also own implementation of static tempfile module via class
        """

        UpgradeImportSystem().replace_module(
            where="^tempfile$", replacement=TempFile, who_name=SELECTOR
        )

        import tempfile

        tmpfile = tempfile.mktemp()
        tmpdir = tempfile.mkdtemp()
        self.assertIn(
            f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp",
            tmpfile,
        )
        self.assertIn(
            f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp",
            tmpdir,
        )
        self.assertFalse(os.path.exists(tmpfile))
        self.assertTrue(os.path.exists(tmpdir))
        self.assertTrue(os.path.isdir(tmpdir))
        os.removedirs(tmpdir)

    def test_method_context_replace_module(self):
        """
        Test if it is able to replace whole module by own implemetation
        Test also own implementation of static tempfile module via class
        """

        with UpgradeImportSystem().replace_module(
            where="^tempfile$", replacement=TempFile, who_name=SELECTOR
        ):
            import tempfile

            tmpfile = tempfile.mktemp()
            tmpdir = tempfile.mkdtemp()
            self.assertIn(
                f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp",
                tmpfile,
            )
            self.assertIn(
                f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp",
                tmpdir,
            )
            self.assertFalse(os.path.exists(tmpfile))
            self.assertTrue(os.path.exists(tmpdir))
            self.assertTrue(os.path.isdir(tmpdir))
            os.removedirs(tmpdir)

    def test_function_replace_module(self):
        """
        Test if it is able to replace whole module by own implemetation
        Test also own implementation of static tempfile module via class
        """

        replace_module(where="^tempfile$", replacement=TempFile, who_name=SELECTOR)
        import tempfile

        tmpfile = tempfile.mktemp()
        tmpdir = tempfile.mkdtemp()
        self.assertIn(
            f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp",
            tmpfile,
        )
        self.assertIn(
            f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp",
            tmpdir,
        )
        self.assertFalse(os.path.exists(tmpfile))
        self.assertTrue(os.path.exists(tmpdir))
        self.assertTrue(os.path.isdir(tmpdir))
        os.removedirs(tmpdir)

    def test_function_context_replace_module(self):
        """
        Test if it is able to replace whole module by own implemetation
        Test also own implementation of static tempfile module via class
        """

        with replace_module(
            where="^tempfile$", replacement=TempFile, who_name=SELECTOR
        ):
            import tempfile

            tmpfile = tempfile.mktemp()
            tmpdir = tempfile.mkdtemp()
            self.assertIn(
                f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp",
                tmpfile,
            )
            self.assertIn(
                f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp",
                tmpdir,
            )
            self.assertFalse(os.path.exists(tmpfile))
            self.assertTrue(os.path.exists(tmpdir))
            self.assertTrue(os.path.isdir(tmpdir))
            os.removedirs(tmpdir)

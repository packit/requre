import builtins
import os
import unittest
from shlex import split

from requre.import_system import UpgradeImportSystem, ReplaceType

SELECTOR = os.path.basename(__file__).rsplit(".", 1)[0]


class ContextManager(unittest.TestCase):
    def test_no_filter(self):
        old_imports = builtins.__import__
        with UpgradeImportSystem():
            import tempfile

            self.assertNotIn("decorated", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())
        assert builtins.__import__ == old_imports

    def test_filter_already_in_sys(self):
        old_imports = builtins.__import__
        with UpgradeImportSystem().upgrade(
            what="tempfile.mktemp",
            replace_type=ReplaceType.DECORATOR,
            replacement=lambda x: lambda: f"decorated {x()}",
        ):
            import tempfile

            self.assertIn("decorated", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())
        assert old_imports == builtins.__import__

    def test_filter_import_random(self):
        old_imports = builtins.__import__

        with UpgradeImportSystem().upgrade(
            what="random.random",
            replace_type=ReplaceType.DECORATOR,
            replacement=lambda x: lambda: f"decorated {x()}",
        ):
            import random

            self.assertIn("decorated", random.random())
            self.assertIn("0.", random.random())
        self.assertIsInstance(random.random(), float)
        assert old_imports == builtins.__import__

    def test_filter_import_from(self):
        with UpgradeImportSystem().upgrade(
            what="shlex.split",
            replace_type=ReplaceType.DECORATOR,
            replacement=lambda x: lambda y: f"mocked {x(y)}",
            add_revert_list=["tests.test_context_manager.split"],
        ):
            self.assertEqual("mocked ['a', 'b']", split("a b"))
        self.assertEqual(["a", "b"], split("a b"))

    def test_filter_import_from_reverted(self):
        with UpgradeImportSystem().upgrade(
            what="shlex.split",
            replace_type=ReplaceType.DECORATOR,
            replacement=lambda x: lambda y: f"mocked {x(y)}",
        ):
            self.assertEqual("mocked ['a', 'b']", split("a b"))
        self.assertEqual(["a", "b"], split("a b"))

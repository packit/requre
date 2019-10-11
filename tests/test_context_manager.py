import builtins
import os
import unittest

from requre.import_system import UpgradeImportSystem, ReplaceType

SELECTOR = os.path.basename(__file__).rsplit(".", 1)[0]


class ContextManager(unittest.TestCase):
    def test_no_filter(self):
        old_imports = builtins.__import__
        with UpgradeImportSystem().upgrade():
            import tempfile

            self.assertNotIn("decorated", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())
        assert builtins.__import__ == old_imports

    def test_filter(self):
        old_imports = builtins.__import__
        with UpgradeImportSystem().upgrade(
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
        ):
            assert old_imports != builtins.__import__
            import tempfile

            self.assertIn("decorated", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())
        assert old_imports == builtins.__import__

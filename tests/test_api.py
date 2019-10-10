import builtins
import os
import unittest

from requre import decorate
from requre.import_system import UpgradeImportSystem

SELECTOR = os.path.basename(__file__).rsplit(".", 1)[0]


class API(unittest.TestCase):
    def test_no_filter(self):
        old_imports = builtins.__import__
        with UpgradeImportSystem():
            import tempfile

            self.assertNotIn("decorated", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())
        assert builtins.__import__ == old_imports

    def test_filter(self):
        old_imports = builtins.__import__
        with UpgradeImportSystem().decorate(
            where="^tempfile$",
            what="mktemp",
            decorator=lambda x: lambda: f"decorated {x()}",
            who_name=SELECTOR,
        ) as upgraded_import_system:
            assert len(upgraded_import_system.filters) == 1
            where, who, what = upgraded_import_system.filters[0]
            assert where == "^tempfile$"
            assert who == {"who_name": SELECTOR}
            assert "mktemp" in what

            assert old_imports != builtins.__import__
            import tempfile

            self.assertIn("decorated", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())
        assert old_imports == builtins.__import__

    def test_function(self):
        old_imports = builtins.__import__
        with decorate(
            where="^tempfile$",
            what="mktemp",
            decorator=lambda x: lambda: f"decorated {x()}",
            who_name=SELECTOR,
        ) as upgraded_import_system:
            assert len(upgraded_import_system.filters) == 1
            where, who, what = upgraded_import_system.filters[0]
            assert where == "^tempfile$"
            assert who == {"who_name": SELECTOR}
            assert "mktemp" in what

            assert old_imports != builtins.__import__
            import tempfile

            self.assertIn("decorated", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())
        assert old_imports == builtins.__import__

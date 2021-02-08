import builtins
from requre import replace, decorate
from requre.import_system import UpgradeImportSystem
from tests.testbase import BaseClass
from tempfile import mktemp as original_mktemp


class TestUpgradeImportSystem(BaseClass):
    def setUp(self) -> None:
        super().setUp()
        self.old_imports = builtins.__import__

    def tearDown(self) -> None:
        builtins.__import__ = self.old_imports
        super().tearDown()

    def test_no_filter(self):
        old_imports = builtins.__import__
        with UpgradeImportSystem():
            import tempfile

            self.assertNotIn("decorated", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())
            tempfile.mktemp = original_mktemp
        assert builtins.__import__ == old_imports

    def test_method_replace(self):
        """
        Test improving of import system with import statement
        Check also debug file output if it contains proper debug data
        """

        UpgradeImportSystem().replace(what="tempfile.mktemp", replacement=lambda: "a")
        import tempfile

        self.assertNotIn("/tmp", tempfile.mktemp())
        self.assertIn("a", tempfile.mktemp())
        tempfile.mktemp = original_mktemp

    def test_method_context_replace(self):
        """
        Test improving of import system with import statement
        Check also debug file output if it contains proper debug data
        """
        with UpgradeImportSystem().replace(
            what="tempfile.mktemp", replacement=lambda: "b"
        ):
            import tempfile

            self.assertNotIn("/tmp", tempfile.mktemp())
            self.assertIn("b", tempfile.mktemp())
            tempfile.mktemp = original_mktemp

    def test_function_context_replace(self):
        """
        Test improving of import system with import statement
        Check also debug file output if it contains proper debug data
        """
        with replace(what="tempfile.mktemp", replacement=lambda: "c"):
            import tempfile

            self.assertNotIn("/tmp", tempfile.mktemp())
            self.assertIn("c", tempfile.mktemp())
            tempfile.mktemp = original_mktemp

    def test_method_decorate(self):
        """
        Test patching by decorator_all_keys, not replacing whole function
        """
        UpgradeImportSystem().decorate(
            what="tempfile.mktemp", decorator=lambda x: lambda: f"decorated_a {x()}"
        )
        import tempfile

        self.assertIn("decorated_a", tempfile.mktemp())
        self.assertIn("/tmp", tempfile.mktemp())
        tempfile.mktemp = original_mktemp

    def test_method_context_decorate(self):
        """
        Test patching by decorator_all_keys, not replacing whole function
        """
        with UpgradeImportSystem().decorate(
            what="tempfile.mktemp", decorator=lambda x: lambda: f"decorated_b {x()}"
        ):
            import tempfile

            self.assertIn("decorated_b", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())
            tempfile.mktemp = original_mktemp

    def test_function_context_decorate(self):
        """
        Test patching by decorator_all_keys, not replacing whole function
        """
        with decorate(
            what="tempfile.mktemp", decorator=lambda x: lambda: f"decorated_c {x()}"
        ):
            import tempfile

            self.assertIn("decorated_c", tempfile.mktemp())
            self.assertIn("/tmp", tempfile.mktemp())
            tempfile.mktemp = original_mktemp

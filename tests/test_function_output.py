import tempfile

from requre.helpers.simple_object import Simple
from requre.storage import PersistentObjectStorage
from requre.utils import run_command, StorageMode
from tests.testbase import BaseClass


class StoreFunctionOutput(BaseClass):
    @staticmethod
    @Simple.decorator_plain()
    def run_command_wrapper(cmd, error_message=None, cwd=None, fail=True, output=False):
        return run_command(
            cmd=cmd, error_message=error_message, cwd=cwd, fail=fail, output=output
        )

    def test_a(self):
        self.assertIn("bin", Simple.decorator_plain()(run_command)("ls /", output=True))
        self.assertIn("bin", Simple.decorator_plain()(run_command)("ls /", output=True))

    def test_run_command_true(self):
        """
        Test if session recording is able to store and return output
        from command via decorating run_command
        """
        output = self.run_command_wrapper(cmd=["true"])
        self.assertTrue(output)
        PersistentObjectStorage().cassette.dump()
        PersistentObjectStorage().cassette.mode = StorageMode.read
        before = str(PersistentObjectStorage().cassette.storage_object)
        output = self.run_command_wrapper(cmd=["true"])
        after = str(PersistentObjectStorage().cassette.storage_object)
        self.assertTrue(output)
        self.assertIn("True", before)
        self.assertNotIn("True", after)
        self.assertGreater(len(before), len(after))

    def test_run_command_output(self):
        """
        check if wrapper returns proper string values in calls
        """
        self.file_name = tempfile.mktemp()
        with open(self.file_name, "w") as fd:
            fd.write("ahoj\n")
        output = self.run_command_wrapper(cmd=["cat", self.file_name], output=True)
        self.assertIn("ahoj", output)
        PersistentObjectStorage().cassette.dump()
        PersistentObjectStorage().cassette.mode = StorageMode.read
        with open(self.file_name, "a") as fd:
            fd.write("cao\n")
        output = self.run_command_wrapper(cmd=["cat", self.file_name], output=True)
        self.assertIn("ahoj", output)
        self.assertNotIn("cao", output)
        PersistentObjectStorage().cassette.mode = StorageMode.write
        output = self.run_command_wrapper(cmd=["cat", self.file_name], output=True)
        self.assertIn("cao", output)
        PersistentObjectStorage().cassette.dump()
        PersistentObjectStorage().cassette.mode = StorageMode.read
        output = self.run_command_wrapper(cmd=["cat", self.file_name], output=True)
        self.assertIn("cao", output)

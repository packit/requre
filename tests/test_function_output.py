import tempfile

from requre.helpers.function_output import run_command_wrapper
from requre.storage import PersistentObjectStorage
from tests.testbase import BaseClass


class StoreFunctionOutput(BaseClass):
    def test_run_command_true(self):
        """
        Test if session recording is able to store and return output
        from command via decorating run_command
        """
        output = run_command_wrapper(cmd=["true"])
        self.assertTrue(output)
        PersistentObjectStorage().dump()
        PersistentObjectStorage()._is_write_mode = False
        before = str(PersistentObjectStorage().storage_object)
        output = run_command_wrapper(cmd=["true"])
        after = str(PersistentObjectStorage().storage_object)
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
        output = run_command_wrapper(cmd=["cat", self.file_name], output=True)
        self.assertIn("ahoj", output)
        PersistentObjectStorage().dump()
        PersistentObjectStorage()._is_write_mode = False
        with open(self.file_name, "a") as fd:
            fd.write("cao\n")
        output = run_command_wrapper(cmd=["cat", self.file_name], output=True)
        self.assertIn("ahoj", output)
        self.assertNotIn("cao", output)
        PersistentObjectStorage()._is_write_mode = True
        output = run_command_wrapper(cmd=["cat", self.file_name], output=True)
        self.assertIn("cao", output)
        PersistentObjectStorage().dump()
        PersistentObjectStorage()._is_write_mode = False
        output = run_command_wrapper(cmd=["cat", self.file_name], output=True)
        self.assertIn("cao", output)

import os
from requre.utils import STORAGE
from requre.helpers.tempfile import TempFile
from tests.testbase import BaseClass


class TestTempFile(BaseClass):
    def testSimple(self):
        output = TempFile.mktemp()
        self.assertIn(f"/tmp/{os.path.basename(STORAGE.storage_file)}/static_tmp_1", output)

    def testChangeFile(self):
        STORAGE.storage_file += ".x"
        output = TempFile.mktemp()
        self.assertIn(f"/tmp/{os.path.basename(STORAGE.storage_file)}/static_tmp_1", output)
        output = TempFile.mktemp()
        self.assertIn(f"/tmp/{os.path.basename(STORAGE.storage_file)}/static_tmp_2", output)
        STORAGE.storage_file += ".y"
        self.assertEqual(TempFile.counter, 2)
        output = TempFile.mktemp()
        self.assertEqual(TempFile.counter, 1)
        self.assertIn(f"/tmp/{os.path.basename(STORAGE.storage_file)}/static_tmp_1", output)
        output = TempFile.mktemp()
        self.assertIn(f"/tmp/{os.path.basename(STORAGE.storage_file)}/static_tmp_2", output)



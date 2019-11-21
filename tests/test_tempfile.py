import os

from requre.helpers.tempfile import TempFile
from requre.storage import PersistentObjectStorage
from tests.testbase import BaseClass


class TestTempFile(BaseClass):
    def testSimple(self):
        output = TempFile.mktemp()
        self.assertIn(
            f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp_1",
            output,
        )

    def testChangeFile(self):
        PersistentObjectStorage().storage_file += ".x"
        output = TempFile.mktemp()
        self.assertIn(
            f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp_1",
            output,
        )
        output = TempFile.mktemp()
        self.assertIn(
            f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp_2",
            output,
        )
        PersistentObjectStorage().storage_file += ".y"
        self.assertEqual(TempFile.counter, 2)
        output = TempFile.mktemp()
        self.assertEqual(TempFile.counter, 1)
        self.assertIn(
            f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp_1",
            output,
        )
        output = TempFile.mktemp()
        self.assertIn(
            f"/tmp/{os.path.basename(PersistentObjectStorage().storage_file)}/static_tmp_2",
            output,
        )

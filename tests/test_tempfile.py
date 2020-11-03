import os

from requre.helpers.tempfile import TempFile
from requre.utils import get_datafile_filename
from tests.testbase import BaseClass


class TestTempFile(BaseClass):
    def setUp(self) -> None:
        super().setUp()
        self.cassette.storage_file = get_datafile_filename(self.id)
        TempFile.set_cassette(self.cassette)

    def testSimple(self):
        output = TempFile._mktemp()
        self.assertIn(
            f"/tmp/{os.path.basename(self.cassette.storage_file)}/static_tmp_1",
            output,
        )

    def testChangeFile(self):
        self.cassette.storage_file = str(self.cassette.storage_file) + ".x"
        output = TempFile._mktemp()
        self.assertIn(
            f"/tmp/{os.path.basename(self.cassette.storage_file)}/static_tmp_1",
            output,
        )
        output = TempFile._mktemp()
        self.assertIn(
            f"/tmp/{os.path.basename(self.cassette.storage_file)}/static_tmp_2",
            output,
        )
        self.cassette.storage_file = str(self.cassette.storage_file) + ".y"
        self.assertEqual(TempFile.counter, 2)
        output = TempFile._mktemp()
        self.assertEqual(TempFile.counter, 1)
        self.assertIn(
            f"/tmp/{os.path.basename(self.cassette.storage_file)}/static_tmp_1",
            output,
        )
        output = TempFile._mktemp()
        self.assertIn(
            f"/tmp/{os.path.basename(self.cassette.storage_file)}/static_tmp_2",
            output,
        )

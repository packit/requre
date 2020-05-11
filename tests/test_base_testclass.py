import os
import shutil

from requre import RequreTestCase
from requre.utils import get_datafile_filename


class CheckBaseTestClass(RequreTestCase):
    def tearDown(self):
        super().tearDown()
        data_file_path = get_datafile_filename(self)
        self.assertTrue(os.path.exists(data_file_path))
        self.assertIn(self.id(), data_file_path.name)
        self.assertIn("test_data", str(data_file_path))
        shutil.rmtree(os.path.dirname(get_datafile_filename(self)))

    def test(self):
        pass

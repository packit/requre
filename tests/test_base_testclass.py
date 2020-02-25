import os
import shutil
from requre import RequreTestCase


class CheckBaseTestClass(RequreTestCase):
    def tearDown(self):
        super().tearDown()
        data_file_path = self.get_datafile_filename()
        self.assertTrue(os.path.exists(data_file_path))
        self.assertIn(self.id(), data_file_path)
        self.assertIn("test_data", data_file_path)
        shutil.rmtree(os.path.dirname(os.path.dirname(self.get_datafile_filename())))

    def test(self):
        pass

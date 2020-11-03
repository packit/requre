import unittest
import git
import shutil
import tempfile
import os
from requre.cassette import Cassette
from requre.modules_decorate_all_methods import (
    record_requests_module,
    record_tempfile_module,
    record_git_module,
)


@record_git_module
@record_tempfile_module
@record_requests_module
class ApplyCommonCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = None
        self.git_url = "git@github.com:packit/hello-world.git"

    @property
    def tempdir(self):
        if not self._tempdir:
            self._tempdir = tempfile.mkdtemp()
        return self._tempdir

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def cassette_teardown(self, cassette: Cassette):
        self.assertIn(
            "tests.test_modules_decorate_all_methods.ApplyCommonCase.test_git.yaml",
            str(cassette.storage_file),
        )

    def test_git(self):
        repo = git.Repo.clone_from(self.git_url, to_path=self.tempdir)
        repo.remotes[0].pull()
        repo.remotes[0].fetch()
        repo.remotes[0].push()
        self.assertIn("static_tmp_1", self.tempdir)
        self.assertIn("hello.spec", os.listdir(self.tempdir))

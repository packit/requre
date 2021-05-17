# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import os
import shutil
import tempfile
import unittest

import git

from requre.helpers import (
    record_git_module,
    record_tempfile_module,
)
from requre.online_replacing import record_requests


@record_git_module
@record_tempfile_module
@record_requests
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

    def test_git(self):
        """When regeneration, tempdir will change, so change the expected output in last assert"""
        repo = git.Repo.clone_from(self.git_url, to_path=self.tempdir)
        repo.remotes[0].pull()
        repo.remotes[0].fetch()
        print(">>", repo.remotes[0].pull, repo.remotes[0].pull.__module__)
        repo.remotes[0].push()
        print(self.tempdir)
        self.assertEqual("/tmp/tmpv1xm25f2", self.tempdir)
        self.assertIn("hello.spec", os.listdir(self.tempdir))

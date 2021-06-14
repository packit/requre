# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import os

import tempfile
from requre.helpers.tempfile import TempFile, MkTemp, MkDTemp
from requre.utils import get_datafile_filename
from tests.testbase import BaseClass
from requre.online_replacing import replace


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


@replace(what="tempfile.mktemp", decorate=MkTemp.decorator_plain())
def new_tempfile():
    return tempfile.mktemp()


@replace(what="tempfile.mkdtemp", decorate=MkDTemp.decorator_plain())
def new_tempdir():
    return tempfile.mkdtemp()


class TempFile_New(BaseClass):
    def test_tempfile(self):
        """When regeneration, tempfile will change, so change the expected output"""
        filename = new_tempfile()
        self.assertFalse(os.path.exists(filename))
        self.assertEqual(filename, "/tmp/tmp5hi99k_2")

    def test_tempdir(self):
        """When regeneration, tempdir will change, so change the expected output"""
        filename = new_tempdir()
        self.assertTrue(os.path.exists(filename))
        self.assertEqual(filename, "/tmp/tmpy7vcma7c")

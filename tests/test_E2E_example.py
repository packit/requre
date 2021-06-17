# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import os
import unittest
import requests
import socket

from requre.helpers import record_requests
from requre.cassette import Cassette, StorageMode

PAGE = "http://example.com"


@record_requests
class WriteCls(unittest.TestCase):
    def cassette_teardown(self, cassette: Cassette):
        self.cassette = cassette
        assert cassette.storage_file
        assert cassette.storage_object
        sf = self.cassette.storage_file
        if sf and os.path.exists(sf):
            os.remove(sf)

    def test(self):
        requests.get(PAGE)


class Write(unittest.TestCase):
    def cassette_setup(self, cassette: Cassette):
        sf = self.cassette.storage_file
        self.cassette.storage_object = {}
        if sf and os.path.exists(sf):
            os.remove(sf)

    def cassette_teardown(self, cassette: Cassette):
        self.cassette = cassette
        assert cassette.storage_file
        assert cassette.storage_object

    @record_requests
    def test(self):
        self.variable = True
        requests.get(PAGE)

    def tearDown(self):
        assert self.variable


@record_requests
class Read(unittest.TestCase):
    def cassette_setup(self, cassette: Cassette):
        if cassette.mode == StorageMode.read:
            setattr(socket, "socket", lambda x: x)

    def cassette_teardown(self, cassette: Cassette):
        self.cassette = cassette
        assert cassette.storage_file
        assert cassette.storage_object

    def test(self):
        requests.get(PAGE)


@record_requests
class TestFail(unittest.TestCase):
    def test(self):
        self.variable = True

    def tearDown(self):
        assert self.variable

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
class TestWriteCls(unittest.TestCase):
    def cassette_teardown(self, cassette: Cassette):
        self.cassette = cassette
        assert cassette.storage_file
        assert cassette.storage_object
        sf = self.cassette.storage_file
        if sf and os.path.exists(sf):
            os.remove(sf)

    def test(self):
        requests.get(PAGE)


class TestWrite(unittest.TestCase):
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
        self.test_executed = True
        requests.get(PAGE)

    def tearDown(self):
        assert self.test_executed


@record_requests
class TestRead(unittest.TestCase):
    def cassette_setup(self, cassette: Cassette):
        # disable network for read mode to prove it read from file
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
        self.test_executed = True

    def tearDown(self):
        assert self.test_executed

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import logging

import pytest

from requre.online_replacing import recording_requests
from requre.utils import StorageMode, get_datafile_filename

logger = logging.getLogger(__name__)


@pytest.fixture
def record_requests_fixture(request):
    storage_file = get_datafile_filename(request.node)
    with recording_requests(storage_file=storage_file) as cassette:
        mode_description = {
            StorageMode.read: "replaying",
            StorageMode.write: "recording",
            StorageMode.append: "appending",
            StorageMode.default: "in default mode",
        }[cassette.mode]
        logger.debug(
            f"Start requre {mode_description} with storage file: {storage_file}"
        )
        yield cassette
        cassette.dump()
        logger.debug(f"End requre {mode_description} with storage file: {storage_file}")

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pytest

from requre.utils import get_datafile_filename


@pytest.fixture
def remove_storage_file(request):
    storage_file = get_datafile_filename(request.node)
    if storage_file.is_file():
        storage_file.unlink()
    return storage_file


@pytest.fixture
def remove_storage_file_after(request):
    storage_file = get_datafile_filename(request.node)
    yield storage_file
    # TODO: found why this were necessary before change of singletons
    # PersistentObjectStorage().cassette.dump()
    if storage_file.is_file():
        storage_file.unlink()


def pytest_collection_modifyitems(items):
    # make sure Duplicated::test test is executed last
    items[:] = sorted(
        items, key=lambda i: i.cls is not None and i.cls.__name__ == "Duplicated"
    )

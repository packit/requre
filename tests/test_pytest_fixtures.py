import pytest

from requre.storage import PersistentObjectStorage
from tests.testbase import network_connection_avalilable

pytest_plugins = ["requre.pytest_fixtures"]


@pytest.mark.skipif(not network_connection_avalilable(), reason="No network connection")
def test_record_requests_fixture(record_requests_fixture):
    import requests

    assert (
        PersistentObjectStorage().storage_file == record_requests_fixture.storage_file
    )
    assert (
        record_requests_fixture.storage_file.name == "test_record_requests_fixture.yaml"
    )
    requests.get("https://google.com")
    assert len(PersistentObjectStorage().storage_object) == 2


@pytest.mark.skipif(not network_connection_avalilable(), reason="No network connection")
def test_record_requests_fixture_different_call(record_requests_fixture):
    import requests

    assert (
        PersistentObjectStorage().storage_file == record_requests_fixture.storage_file
    )
    assert (
        record_requests_fixture.storage_file.name
        == "test_record_requests_fixture_different_call.yaml"
    )
    requests.get("https://fedoraproject.org")
    assert len(PersistentObjectStorage().storage_object) == 2


@pytest.mark.skipif(not network_connection_avalilable(), reason="No network connection")
def test_record_requests_fixture_write(
    remove_storage_file, record_requests_fixture, remove_storage_file_after
):
    import requests

    assert (
        PersistentObjectStorage().storage_file == record_requests_fixture.storage_file
    )
    assert remove_storage_file == record_requests_fixture.storage_file
    assert remove_storage_file == remove_storage_file_after
    assert (
        record_requests_fixture.storage_file.name
        == "test_record_requests_fixture_write.yaml"
    )
    requests.get("https://google.com")
    assert len(PersistentObjectStorage().storage_object) == 2


@pytest.mark.skipif(not network_connection_avalilable(), reason="No network connection")
def test_record_requests_fixture_different_call_write(
    remove_storage_file, record_requests_fixture, remove_storage_file_after
):
    import requests

    assert (
        PersistentObjectStorage().storage_file == record_requests_fixture.storage_file
    )
    assert remove_storage_file == record_requests_fixture.storage_file
    assert remove_storage_file == remove_storage_file_after
    assert (
        record_requests_fixture.storage_file.name
        == "test_record_requests_fixture_different_call_write.yaml"
    )
    requests.get("https://fedoraproject.org")
    assert len(PersistentObjectStorage().storage_object) == 2

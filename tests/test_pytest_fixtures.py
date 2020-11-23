import pytest

from requre.storage import PersistentObjectStorage
from tests.testbase import network_connection_available

pytest_plugins = ["requre.pytest_fixtures"]


@pytest.mark.skipif(not network_connection_available(), reason="No network connection")
def test_record_requests_fixture(record_requests_fixture):
    import requests

    # ensure that storage_file is  not propagated to Singleton
    assert (
        PersistentObjectStorage().cassette.storage_file
        != record_requests_fixture.storage_file
    )
    assert (
        record_requests_fixture.storage_file.name == "test_record_requests_fixture.yaml"
    )
    requests.get("https://google.com")


@pytest.mark.skipif(not network_connection_available(), reason="No network connection")
def test_record_requests_fixture_different_call(record_requests_fixture):
    import requests

    assert (
        record_requests_fixture.storage_file.name
        == "test_record_requests_fixture_different_call.yaml"
    )
    requests.get("https://fedoraproject.org")


@pytest.mark.skipif(not network_connection_available(), reason="No network connection")
def test_record_requests_fixture_write(
    remove_storage_file, record_requests_fixture, remove_storage_file_after
):
    import requests

    assert remove_storage_file == record_requests_fixture.storage_file
    assert remove_storage_file == remove_storage_file_after
    assert (
        record_requests_fixture.storage_file.name
        == "test_record_requests_fixture_write.yaml"
    )
    requests.get("https://google.com")


@pytest.mark.skipif(not network_connection_available(), reason="No network connection")
def test_record_requests_fixture_different_call_write(
    remove_storage_file, record_requests_fixture, remove_storage_file_after
):
    import requests

    assert remove_storage_file == record_requests_fixture.storage_file
    assert remove_storage_file == remove_storage_file_after
    assert (
        record_requests_fixture.storage_file.name
        == "test_record_requests_fixture_different_call_write.yaml"
    )
    requests.get("https://fedoraproject.org")

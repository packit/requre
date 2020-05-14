import logging
import os
from unittest import TestCase
from requre.storage import PersistentObjectStorage
from requre.cassette import StorageKeysInspectOuter, StorageKeysInspectSimple
from requre.utils import get_datafile_filename

logger = logging.getLogger(__name__)


class RequreTestCase(TestCase):
    """
    This is base unittest TestCase what will help you to store requre storage files
    It will create directory structre test_data/TEST_FILE_NAME in a directory where
    test is stored. inside this subdir. there is created storage file via calling
    self.id()
    suffixed by yaml
    """

    def setUp(self):
        super().setUp()
        response_file = get_datafile_filename(self)
        os.makedirs(os.path.dirname(response_file), mode=0o777, exist_ok=True)
        self.cassette = PersistentObjectStorage().cassette
        self.cassette.storage_file = response_file

    def tearDown(self):
        self.cassette.dump()
        super().tearDown()


class RequreTestCaseOuterKeys(RequreTestCase):
    """
    This is base unittest TestCase what will help you to store requre storage files
    It will create directory structre test_data/TEST_FILE_NAME in a directory where
    test is stored. inside this subdir. there is created storage file via calling
    self.id()
    suffixed by yaml

    Using Simplier Storage keys
    It tries to avoid storing of unwanted stack information in your test, testing stack or project.
    It uses PWD to differentiate what is wanted and unwanted.
    """

    def setUp(self):
        super().setUp()
        self.cassette.data_miner.key_stategy_cls = StorageKeysInspectOuter


class RequreTestCaseSimple(RequreTestCase):
    """
    This is base unittest TestCase what will help you to store requre storage files
    It will create directory structre test_data/TEST_FILE_NAME in a directory where
    test is stored. inside this subdir. there is created storage file via calling
    self.id()
    suffixed by yaml

    it uses very simple keys for storage files, should be more robust from perspective
    of running test, less robust from perspective of test debugging.
    Beause it can match antother requrest if there will be more queries.
    """

    def setUp(self):
        super().setUp()
        self.cassette.data_miner.key_stategy_cls = StorageKeysInspectSimple

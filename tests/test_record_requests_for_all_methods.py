import math
import unittest
from pathlib import Path

import requests

from requre.cassette import Cassette
from requre.helpers.simple_object import Simple
from requre.online_replacing import (
    record_requests_for_all_methods,
    apply_decorator_to_all_methods,
    replace_module_match,
)


@apply_decorator_to_all_methods(
    replace_module_match(what="math.sin", decorate=Simple.decorator_plain())
)
@record_requests_for_all_methods()
class DecoratorClassApplyMultipleDecorators(unittest.TestCase):
    def use_math_and_requests(self):
        sin_output = math.sin(1.5)
        self.assertAlmostEqual(0.9974949866040544, sin_output, delta=0.0005)

        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)

    def test_read(self, cassette: Cassette):
        self.assertIn("math", cassette.storage_object)
        self.assertIn("requests.sessions", cassette.storage_object)
        # move the following call to the beginning when regenerating
        self.use_math_and_requests()

    def test_write(self, cassette: Cassette):
        self.assertIsNotNone(cassette)

        self.use_math_and_requests()

        self.assertIn("math", cassette.storage_object)
        self.assertIn("requests.sessions", cassette.storage_object)

        self.assertFalse(Path(cassette.storage_file).exists())
        cassette.dump()
        self.assertTrue(Path(cassette.storage_file).exists())
        Path(cassette.storage_file).unlink()


@record_requests_for_all_methods()
class DecoratorRecordRequestForAllMethods(unittest.TestCase):
    def use_requests(self):
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)

    def test_read(self, cassette: Cassette):
        self.assertIn("requests.sessions", cassette.storage_object)
        # move the following call to the beginning when regenerating
        self.use_requests()

    def test_write(self, cassette: Cassette):
        self.assertIsNotNone(cassette)

        self.use_requests()

        self.assertIn("requests.sessions", cassette.storage_object)

        self.assertFalse(Path(cassette.storage_file).exists())
        cassette.dump()
        self.assertTrue(Path(cassette.storage_file).exists())
        Path(cassette.storage_file).unlink()


@record_requests_for_all_methods
class DecoratorRecordRequestForAllMethodsWithoutParenthesis(unittest.TestCase):
    def use_requests(self):
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)

    def test_read(self, cassette: Cassette):
        self.assertIn("requests.sessions", cassette.storage_object)
        # move the following call to the beginning when regenerating
        self.use_requests()

    def test_write(self, cassette: Cassette):
        self.assertIsNotNone(cassette)

        self.use_requests()

        self.assertIn("requests.sessions", cassette.storage_object)

        self.assertFalse(Path(cassette.storage_file).exists())
        cassette.dump()
        self.assertTrue(Path(cassette.storage_file).exists())
        Path(cassette.storage_file).unlink()


@record_requests_for_all_methods(regexp_method_pattern="test_regex.*")
class DecoratorRecordRequestForAllMethodsDifferentRegex(unittest.TestCase):
    def some_method(self):
        pass

    def use_requests(self):
        response = requests.get("http://example.com")
        self.assertIn("This domain is for use", response.text)

    def test_without_decorator(self, cassette: Cassette = None):
        self.assertIsNone(cassette)

    def test_regex_read(self, cassette: Cassette):
        self.assertIn("requests.sessions", cassette.storage_object)
        # move the following call to the beginning when regenerating
        self.use_requests()

    def test_regex_write(self, cassette: Cassette):
        self.assertIsNotNone(cassette)

        self.use_requests()

        self.assertIn("requests.sessions", cassette.storage_object)

        self.assertFalse(Path(cassette.storage_file).exists())
        cassette.dump()
        self.assertTrue(Path(cassette.storage_file).exists())
        Path(cassette.storage_file).unlink()
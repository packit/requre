from unittest import TestCase
from requre.cassette import CassetteExecution


class Execution(TestCase):
    def testCreate(self):
        ce = CassetteExecution()
        ce.function = lambda: "ahoj"
        ce.cassette = "nothing"
        self.assertEqual("ahoj", ce.function())
        self.assertEqual("ahoj", ce())

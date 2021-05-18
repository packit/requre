# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import random
import unittest
from requre import record


@record(what="random.random")
class Test(unittest.TestCase):
    def test(self):
        self.assertEqual(0.8682724996217076, random.random())

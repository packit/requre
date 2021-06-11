# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import random


def hello(text="Hi! "):
    return text


def inc(value):
    return value + 1


class dynamic:
    def __init__(self):
        self.text = "called"

    def __getattr__(self, item):
        return lambda: item.upper()


def random_number():
    return random.random()


def another_random_number():
    return random.random()

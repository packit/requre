# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import unittest

from requre.record_and_replace import make_generic


class ApplyCommonCase(unittest.TestCase):
    def test_simple_use(self):
        @make_generic
        def add_one(fce):
            def fce_to_return():
                return fce() + 1

            return fce_to_return

        @add_one
        def simple_use():
            return 0

        assert simple_use() == 1

    def test_parenthesis_use(self):
        @make_generic
        def add_one(fce):
            def fce_to_return():
                return fce() + 1

            return fce_to_return

        @add_one()
        def parenthesis_use():
            return 0

        assert parenthesis_use() == 1

    def test_parenthesis_use_with_args(self):
        @make_generic
        def add_something(add):
            def decorator_to_return(fce):
                def fce_to_return():
                    return fce() + add

                return fce_to_return

            return decorator_to_return

        @add_something(1)
        def parenthesis_use_with_args():
            return 0

        assert parenthesis_use_with_args() == 1

    def test_parenthesis_use_with_kwargs(self):
        @make_generic
        def add_something(add):
            def decorator_to_return(fce):
                def fce_to_return():
                    return fce() + add

                return fce_to_return

            return decorator_to_return

        @add_something(add=1)
        def parenthesis_use_with_kwargs():
            return 0

        assert parenthesis_use_with_kwargs() == 1

    def test_class_simple_use(self):
        @make_generic
        def add_one(fce):
            def fce_to_return(*args, **kwargs):
                return fce(*args, **kwargs) + 1

            return fce_to_return

        @add_one
        class SimpleUse:
            def test_simple_use(self):
                # We match `test.*` methods by default
                return 0

        assert SimpleUse().test_simple_use() == 1

    def test_class_parenthesis(self):
        @make_generic
        def add_one(fce):
            def fce_to_return(*args, **kwargs):
                return fce(*args, **kwargs) + 1

            return fce_to_return

        @add_one()
        class SimpleUse:
            def test_simple_use(self):
                # We match `test.*` methods by default
                return 0

        assert SimpleUse().test_simple_use() == 1

    def test_class_parenthesis_use_with_args(self):
        @make_generic
        def add_something(add):
            def decorator_to_return(fce):
                def fce_to_return(*args, **kwargs):
                    return fce(*args, **kwargs) + add

                return fce_to_return

            return decorator_to_return

        @add_something(1)
        class SimpleUse:
            def test_simple_use(self):
                # We match `test.*` methods by default
                return 0

        assert SimpleUse().test_simple_use() == 1

    def test_class_parenthesis_use_with_kwargs(self):
        @make_generic
        def add_something(add):
            def decorator_to_return(fce):
                def fce_to_return(*args, **kwargs):
                    return fce(*args, **kwargs) + add

                return fce_to_return

            return decorator_to_return

        @add_something(add=1)
        class SimpleUse:
            def test_simple_use(self):
                return 0

        assert SimpleUse().test_simple_use() == 1

    def test_class_parenthesis_use_with_regexp_method_pattern_not_set(self):
        @make_generic
        def add_something(add):
            def decorator_to_return(fce):
                def fce_to_return(*args, **kwargs):
                    return fce(*args, **kwargs) + add

                return fce_to_return

            return decorator_to_return

        @add_something(add=1)
        class SimpleUse:
            def simple_use(self):
                return 0

            def test_simple_use(self):
                # We match `test.*` methods by default
                return 0

        assert SimpleUse().simple_use() == 0
        assert SimpleUse().test_simple_use() == 1

    def test_class_parenthesis_use_with_regexp_method_pattern_set(self):
        @make_generic
        def add_something(add):
            def decorator_to_return(fce):
                def fce_to_return(*args, **kwargs):
                    return fce(*args, **kwargs) + add

                return fce_to_return

            return decorator_to_return

        @add_something(add=1, regexp_method_pattern="simple.*")
        class SimpleUse:
            def simple_use(self):
                return 0

            def test_simple_use(self):
                # We match `test.*` methods by default
                return 0

        assert SimpleUse().simple_use() == 1
        assert SimpleUse().test_simple_use() == 0

    def test_double_use_on_decorator(self):
        @make_generic
        @make_generic
        def add_one(fce):
            def fce_to_return():
                return fce() + 1

            return fce_to_return

        @add_one
        def simple_use():
            return 0

        assert simple_use() == 1

    def test_chain_of_decorators(self):
        @make_generic
        def plus_one(fce):
            def fce_to_return():
                return fce() + 1

            return fce_to_return

        @make_generic
        def add_one(fce):
            return plus_one(fce)

        @add_one
        def simple_use():
            return 0

        assert simple_use() == 1

    def test_parenthesis_double_use_with_args(self):
        @make_generic
        @make_generic
        def add_something(add):
            def decorator_to_return(fce):
                def fce_to_return():
                    return fce() + add

                return fce_to_return

            return decorator_to_return

        @add_something(1)
        def parenthesis_use_with_args():
            return 0

        assert parenthesis_use_with_args() == 1

    def test_use_with_args_chain_decorators(self):
        @make_generic
        def add_something(add):
            def decorator_to_return(fce):
                def fce_to_return():
                    return fce() + add

                return fce_to_return

            return decorator_to_return

        @make_generic
        def add_one(fce):
            return add_something(1)(fce)

        @add_one
        def parenthesis_use_with_args():
            return 0

        assert parenthesis_use_with_args() == 1

    def test_parenthesis_use_with_args_not_set(self):
        """
        When using with optional arguments,
        you need to use `if _func is None:....` trick in your decorator.
        """

        @make_generic
        def add_something(_func=None, add=1):
            def decorator_to_return(fce):
                def fce_to_return():
                    return fce() + add

                return fce_to_return

            if _func is None:
                # @add_something()
                return decorator_to_return
            else:
                # @add_something
                return decorator_to_return(_func)

        @add_something()
        def parenthesis_use_with_args():
            return 0

        assert parenthesis_use_with_args() == 1

    def test_simple_use_with_args_not_set(self):
        """
        When using with optional arguments,
        you need to use `if _func is None:....` trick in your decorator.
        """

        @make_generic
        def add_something(_func=None, add=1):
            def decorator_to_return(fce):
                def fce_to_return():
                    return fce() + add

                return fce_to_return

            if _func is None:
                # @add_something()
                return decorator_to_return
            else:
                # @add_something
                return decorator_to_return(_func)

        @add_something
        def parenthesis_use_with_args():
            return 0

        assert parenthesis_use_with_args() == 1

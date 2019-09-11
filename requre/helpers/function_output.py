# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import functools
import inspect
from typing import Callable, Any
from requre.utils import get_if_recording, STORAGE, run_command


def store_function_output(func: Callable) -> Any:
    @functools.wraps(func)
    def recorded_function(*args, **kwargs):
        if not get_if_recording():
            return func(*args, **kwargs)
        else:
            keys = [inspect.getmodule(func).__name__, func.__name__]
            # removed extension because using tempfiles
            # + [x for x in args if isinstance(int, str)] + [f"{k}={v}" for k, v in kwargs.items()]

            if STORAGE.is_write_mode:
                output = func(*args, **kwargs)
                STORAGE.store(keys, output)

            else:
                output = STORAGE.read(keys)
            return output
    return recorded_function


@store_function_output
def run_command_wrapper(cmd, error_message=None, cwd=None, fail=True, output=False):
    return run_command(
        cmd=cmd, error_message=error_message, cwd=cwd, fail=fail, output=output
    )

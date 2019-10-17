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
from typing import Callable, Any

from requre.utils import get_if_recording, STORAGE, run_command
from requre.objects import ObjectStorage
from requre.storage import DataMiner, original_time


def store_function_output(func: Callable) -> Any:
    fn_keys = ["store_function_output"]

    @functools.wraps(func)
    def recorded_function(*args, **kwargs):
        if not get_if_recording():
            return func(*args, **kwargs)
        else:
            keys = ObjectStorage.get_base_keys(func) + fn_keys
            # removed extension because using tempfiles
            # + [x for x in args if isinstance(int, str)] + [f"{k}={v}" for k, v in kwargs.items()]

            if STORAGE.is_write_mode:
                time_before = original_time()
                output = func(*args, **kwargs)
                time_after = original_time()
                STORAGE.store(keys, output)
                DataMiner().metadata = {DataMiner.LATENCY_KEY: time_after - time_before}
            else:
                output = STORAGE.read(keys)
            return output

    return recorded_function


@store_function_output
def run_command_wrapper(cmd, error_message=None, cwd=None, fail=True, output=False):
    return run_command(
        cmd=cmd, error_message=error_message, cwd=cwd, fail=fail, output=output
    )

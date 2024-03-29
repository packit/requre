# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import inspect
import logging
import shlex
import subprocess
from enum import Enum
from pathlib import Path

from _pytest.python import Function

from requre.constants import RELATIVE_TEST_DATA_DIRECTORY, DEFAULT_SUFIX
from requre.exceptions import PersistentStorageException

logger = logging.getLogger(__name__)


class StorageMode(Enum):
    default = 0
    read = 1
    write = 2
    append = 3


def run_command(cmd, error_message=None, cwd=None, fail=True, output=False):
    """
    subprocess wrapper, copied from packit, for higher level handling of executiong commands,
    :param cmd:
    :param error_message:
    :param cwd:
    :param fail:
    :param output:
    :return:
    """
    if not isinstance(cmd, list):
        cmd = shlex.split(cmd)

    logger.debug("cmd = '%s'", " ".join(cmd))

    cwd = cwd or str(Path.cwd())
    error_message = error_message or f"Command {cmd} failed."

    shell = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        cwd=cwd,
        universal_newlines=True,
    )

    if not output:
        # output is returned, let the caller process it
        logger.debug("%s", shell.stdout)
    stderr = shell.stderr.strip()
    if stderr:
        logger.error("%s", shell.stderr)

    if shell.returncode != 0:
        logger.error("Command %s failed", shell.args)
        logger.error("%s", error_message)
        if fail:
            raise PersistentStorageException(
                f"Command {shell.args!r} failed: {error_message}"
            )
        success = False
    else:
        success = True

    if not output:
        return success
    return shell.stdout


class Replacement:
    def __init__(self, name, key, parent, one_filter, replacement) -> None:
        self.name = name
        self.key = key
        self.parent = parent
        self.filter = one_filter
        self.replacement = replacement


def get_module_of_previous_context():
    current_ctx = inspect.currentframe()
    while True:
        current_ctx = current_ctx.f_back
        frameinfo_args = (current_ctx,) + inspect.getframeinfo(current_ctx, 1)
        frameinfo = inspect.FrameInfo(*frameinfo_args)
        module = inspect.getmodule(frameinfo[0])
        if module and not module.__name__.startswith("requre"):
            return module


def get_class_that_defined_method(meth):
    """
    return class for given method meth

    :param meth: method where we would like to find class, where is methond defined
    :returns: class or None
    """
    # https://stackoverflow.com/questions/961048/get-class-that-defined-method
    for cls in inspect.getmro(meth.im_class):
        if meth.__name__ in cls.__dict__:
            return cls
    return None


def get_datafile_filename(obj, suffix=DEFAULT_SUFIX):
    """
    get default path for data files.
    It consist of 3 pieces: "location of test"/test_data/test_file_name/"test_id or function name"

    :param obj: object from which try to guess name of file and functioon
    :return: str with path where to store data_file
    """

    try:
        if isinstance(obj, Function):
            # pytest fixture
            current_fn_file_name = obj.module.__file__
        else:
            # try to get filename via class if possible (pytest way)
            current_fn_file_name = inspect.getfile(obj.__class__)
    except (AttributeError, TypeError):
        # try to get filename from object
        current_fn_file_name = inspect.getfile(obj)

    real_path_dir = Path(current_fn_file_name).parent.absolute()
    test_file_name = Path(current_fn_file_name).name.rsplit(".", 1)[0]
    old_test_name = None
    try:
        # try to use object.id() function (it is defined inside pytest unittests)
        old_test_name = test_name = obj.id()
        # use just class and function as indentifier of file
        cls_name = obj.__class__.__name__
        test_name = cls_name + test_name.rsplit(cls_name, 1)[1]
    except AttributeError:
        try:
            if isinstance(obj, Function):
                # pytest fixture
                test_name = obj.name
            else:
                # try to use __name__ of the object (typically name of function)
                test_name = obj.__name__
        except AttributeError:
            # if not possible, use this name as name of data file
            test_name = "static_test_data_name"
    testdata_dirname = real_path_dir / RELATIVE_TEST_DATA_DIRECTORY / test_file_name
    # BACKWARD COMPATIBILITY (read mode): check if a file using a full self.id is present
    if old_test_name:
        old_store_path = testdata_dirname / f"{old_test_name}.{suffix}"
        if old_store_path.exists():
            return old_store_path
    return testdata_dirname / f"{test_name}.{suffix}"

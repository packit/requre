#!/usr/bin/python3

import os
import sys
import shutil
import click
import importlib.util
import atexit

from requre.import_system import upgrade_import_system, UpgradeImportSystem
from requre.utils import STORAGE
from requre.storage import DataMiner
from requre.constants import (
    ENV_REPLACEMENT_FILE,
    ENV_STORAGE_FILE,
    ENV_DEBUG,
    REPLACE_DEFAULT_KEY,
    ENV_APPLY_LATENCY,
)

"""
This is command line tool for E2E and functional testing to enable requre
without access python code.

It apply itself as sitecustomize.py script
to user home path:
   ~/.local/lib/python{version}/site-packages
or to system path via option --system:
   /usr/lib/python{version}/site-packages

when tool is installed call python code with enviroment variables:
 RESPONSE_FILE - Storage file path for session recording.
        In case file does not exists, it will use write mode
        In case file exists, it will use read mode for Storage
 REPLACEMENT_FILE - Replacement file  path for import system.
        It is important to have there set variable FILTERS what will
        be used as replacements list for upgrade_import_system function.
        For more details see doc: https://github.com/packit-service/requre/
 DEBUG - if set, print debugging information, fi requre is applied
 LATENCY - apply latency waits for test, to have simiar test timing
        It is important when using some async/messaging calls
"""

FILE_NAME = "sitecustomize.py"


def debug_print(*args):
    if os.getenv(ENV_DEBUG):
        print("REQURE DEBUG:", *args, file=sys.__stderr__)


def apply_fn():
    """
    This function is used when installed as  sitecustomize.py script
    to enable replacing system, please set env vars RESPONSE_FILE
    REPLACEMENT_FILE, see doc string of this file
    """
    # file name of storage file
    storage_file = os.getenv(ENV_STORAGE_FILE)
    # file name of replaces for updated import system
    replacement_file = os.getenv(ENV_REPLACEMENT_FILE)
    if_latency = os.getenv(ENV_APPLY_LATENCY)
    debug_print(
        f"You have patched version of your python by requre project "
        f"(python {sys.version_info.major}.{sys.version_info.minor}, {__file__}) "
    )
    if not (storage_file and replacement_file):
        debug_print(
            f"\tYou have to set {ENV_STORAGE_FILE} and "
            f"{ENV_REPLACEMENT_FILE} env variables to work properly"
        )
    else:
        if not os.path.exists(replacement_file):
            raise FileExistsError(
                f"{replacement_file} has to exist to work properly "
                f"(python file with replacements definition)"
            )
        if if_latency:
            debug_print("Use latency for function calls")
            DataMiner().use_latency = True
        STORAGE.storage_file = storage_file
        # register dump command, when python finish
        atexit.register(STORAGE.dump)

        spec = importlib.util.spec_from_file_location("replacements", replacement_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, REPLACE_DEFAULT_KEY):
            replacement = getattr(module, REPLACE_DEFAULT_KEY)
            debug_print(f"Replaces: {replacement}")
            if isinstance(replacement, UpgradeImportSystem):
                debug_print(
                    f"{REPLACE_DEFAULT_KEY} is {UpgradeImportSystem.__name__} object"
                )
            elif isinstance(replacement, list):
                debug_print(
                    f"{REPLACE_DEFAULT_KEY} is list of replacements, apply upgrading"
                )
                upgrade_import_system(filters=replacement)
            else:
                raise ValueError(
                    f"Bad type of {REPLACE_DEFAULT_KEY}, see documentation"
                )
        else:
            raise AttributeError(
                f"in {replacement_file} there is not defined '{REPLACE_DEFAULT_KEY}' variable"
            )


def get_current_python_version():
    """
    Get current running version of python

    :return: str in format X.Y
    """
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def path_to_python_customize(version: str, global_path: bool = False):
    """
    return path to sitecustomize.py file based on python version and
    if it should be local for user or installed to system

    :param version: str: version string
    :param global_path: bool - if apply it to whole system
    :return: str with full path to python file
    """
    if global_path:
        site_path = f"/usr/lib/python{version}/site-packages"
    else:
        site_path = os.path.expanduser(f"~/.local/lib/python{version}/site-packages")
        os.makedirs(site_path, exist_ok=True)
    customize_file = os.path.join(site_path, FILE_NAME)
    return customize_file


def patch_verify(pathname: str):
    """
    Check if patch file already exists
    :param pathname: path to sitecustomization file
    :return: bool if exists
    """
    return os.path.exists(pathname)


@click.group("requre")
@click.option(
    "--version", default=get_current_python_version(), help="Version of python to patch"
)
@click.option(
    "--system",
    is_flag=True,
    default=False,
    help="Use system python path, instead of user home dir",
)
@click.pass_context
def requre_base(ctx, version, system):
    ctx.obj = {FILE_NAME: path_to_python_customize(version=version, global_path=system)}


@requre_base.command()
@click.pass_context
def verify(ctx):
    if patch_verify(ctx.obj[FILE_NAME]):
        click.echo(f"Python patched (file: {ctx.obj[FILE_NAME]})")
    else:
        raise click.ClickException(f"Python not patched (file: {ctx.obj[FILE_NAME]})")


@requre_base.command()
@click.pass_context
def apply(ctx):
    if patch_verify(ctx.obj[FILE_NAME]):
        raise click.ClickException(
            f"Python already patched (file: {ctx.obj[FILE_NAME]})"
        )
    else:
        click.echo(f"Applying import patch to python (file: {ctx.obj[FILE_NAME]})")
        shutil.copy(__file__, ctx.obj[FILE_NAME])


@requre_base.command()
@click.pass_context
def clean(ctx):
    if patch_verify(ctx.obj[FILE_NAME]):
        os.remove(ctx.obj[FILE_NAME])
    else:
        raise click.ClickException(
            f"Patch not applied (file: {ctx.obj[FILE_NAME]}), nothing to do"
        )


if __name__ == "__main__" or not (__file__ and __file__.endswith(FILE_NAME)):
    requre_base()
else:
    apply_fn()

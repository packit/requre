#!/usr/bin/python3

import os
import sys
import shutil
import click
import importlib.util
import atexit
from typing import Any
import yaml
import builtins

from requre.import_system import UpgradeImportSystem
from requre.postprocessing import DictProcessing, TarFilesSimilarity
from requre.storage import PersistentObjectStorage
from requre.constants import (
    ENV_REPLACEMENT_FILE,
    ENV_STORAGE_FILE,
    ENV_DEBUG,
    REPLACE_DEFAULT_KEY,
    ENV_APPLY_LATENCY,
    ENV_REPLACEMENT_NAME,
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
 REPLACEMENT_VAR - Overrides default value of variable in REPLACEMENT_FILE
        what will be used as replacement variable.
 DEBUG - if set, print debugging information, fi requre is applied
 LATENCY - apply latency waits for test, to have simiar test timing
        It is important when using some async/messaging calls
"""

FILE_NAME = "sitecustomize.py"


def debug_print(*args):
    if os.getenv(ENV_DEBUG):
        print("REQURE DEBUG:", *args, file=sys.__stderr__)


def raise_error(ret_code: int, msg: Any):
    """
    When installed as sitecustomization.py, exceptions are not propagated to main process
    process, ends successfully, although it contains traceback/

    :param ret_code: return code to return
    :param msg: message to write to stderr
    :return: None
    """
    print(msg)
    os._exit(ret_code)


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
    replacement_var = os.getenv(ENV_REPLACEMENT_NAME, REPLACE_DEFAULT_KEY)
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
            PersistentObjectStorage().cassette.data_miner.use_latency = True
        PersistentObjectStorage().cassette.storage_file = storage_file
        spec = importlib.util.spec_from_file_location("replacements", replacement_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        replacement = None
        if hasattr(module, replacement_var):
            replacement = getattr(module, replacement_var)
            debug_print(f"Replaces: {replacement}")
            if isinstance(replacement, UpgradeImportSystem):
                debug_print(
                    f"{replacement_var} is {UpgradeImportSystem.__name__} object"
                )
            else:
                raise_error(126, f"Bad type of {replacement_var}, see documentation")
        else:
            raise_error(
                125,
                f"in {replacement_file} there is not defined '{replacement_var}' variable",
            )
        # register dump command, when python finish
        if replacement:
            atexit.register(replacement.cassette.dump)


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


@requre_base.command()
@click.option(
    "--replaces",
    help="match_string:key:type_of_value:value = Substitution query in format, "
    "where match_string is in format of selecting dictionary keys:"
    "selector1%selector2, type_of_value is some object what is serializable "
    "and part or builtins module (e.g. int)",
    multiple=True,
)
@click.argument("files", nargs=-1, type=click.File("r"))
@click.option(
    "--dry-run", is_flag=True, default=False, help="Do not write changes back"
)
@click.option(
    "--simplify",
    is_flag=True,
    default=False,
    help="Simplify dict structure if possible (experimental feature)",
)
def purge(replaces, files, dry_run, simplify):
    for one_file in files:
        click.echo(f"Processing file: {one_file.name}")
        object_representation = yaml.safe_load(one_file)
        processor = DictProcessing(object_representation)
        for item in replaces:
            click.echo(f"\tTry to apply: {item}")
            selector_str, key, type_of_value, value = item.split(":", 3)
            selector_list = [] if not selector_str else selector_str.split("%")
            # retype the output object to proper type ()
            value = getattr(builtins, type_of_value)(value)
            for matched in processor.match(selector=selector_list):
                click.echo(f"\t\tMatched {selector_list}")
                processor.replace(obj=matched, key=key, value=value)
        if simplify:
            processor.simplify()
        if not dry_run:
            click.echo(f"Writing content back to file: {one_file.name}")
            with open(one_file.name, mode="w") as outfile:
                outfile.write(yaml.safe_dump(object_representation))


@requre_base.command()
@click.argument("base_dir", nargs=1, type=click.Path())
@click.option(
    "--dry-run", is_flag=True, default=False, help="Do not write changes back"
)
def create_symlinks(base_dir, dry_run):
    click.echo(f"Processing base dir: {base_dir}")
    tar_dict = TarFilesSimilarity(base_dir)
    similar = tar_dict.find_same()
    for k, v in similar.items():
        if k is not None:
            click.echo(f"hash: {k}")
            for item in v:
                click.echo(f"\t{item.replace(base_dir, '').strip(os.path.sep)}")
    if dry_run:
        click.echo("dry-run mode: just listing similar files")
        return
    click.echo("Created symlinks for listed files")
    tar_dict.symlink_same_files()


if __name__ == "__main__" or not (__file__ and __file__.endswith(FILE_NAME)):
    requre_base()
else:
    apply_fn()

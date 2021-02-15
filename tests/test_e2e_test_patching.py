import os
import unittest
import tempfile
import shutil
import time
from requre.utils import run_command
from requre.exceptions import PersistentStorageException
from requre.constants import (
    ENV_REPLACEMENT_FILE,
    ENV_STORAGE_FILE,
    ENV_APPLY_LATENCY,
    ENV_REPLACEMENT_NAME,
)


CMD_RELATIVE = f"""python3 {os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                "requre", "requre_patch.py")}"""
CMD_TOOL = "requre-patch"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def is_sudo_possible():
    random_file = "/usr/bin/test_superuser"
    try:
        run_command(f"sudo -n touch {random_file}")
    except (PersistentStorageException, FileNotFoundError):
        return False
    run_command(f"sudo rm {random_file}")
    return True


def is_requre_installed():
    try:
        run_command(f"{CMD_TOOL} --help")
    except (PersistentStorageException, FileNotFoundError):
        return False
    return True


@unittest.skipUnless(
    is_requre_installed(), "not possible to run without installed requre"
)
class InstalledCommand(unittest.TestCase):
    def setUp(self) -> None:
        run_command(cmd=f"{CMD_RELATIVE} clean", fail=False)

    def tearDown(self) -> None:
        run_command(cmd=f"{CMD_RELATIVE} clean", fail=False)

    def test_not_installed(self):
        self.assertRaises(
            PersistentStorageException, run_command, cmd=f"{CMD_TOOL} verify"
        )

    def test_install(self):
        self.assertIn(
            "Applying import patch",
            run_command(cmd=f"{CMD_TOOL} apply", fail=False, output=True),
        )

    def test_verify_user(self):
        self.test_install()
        output = run_command(cmd=f"{CMD_RELATIVE} verify", output=True)
        self.assertIn("Python patched", output)
        self.assertIn(os.path.expanduser("~/.local/lib/python"), output)

    def test_verify_system(self):
        self.test_install()
        self.assertRaises(
            PersistentStorageException,
            run_command,
            cmd=f"{CMD_RELATIVE} --system verify",
        )


class NoApplied(unittest.TestCase):
    def setUp(self) -> None:
        run_command(cmd=f"{CMD_RELATIVE} clean", fail=False)

    def test_help(self):
        run_command(cmd=f"{CMD_RELATIVE}")

    def test_bad_command(self):
        self.assertRaises(
            PersistentStorageException, run_command, cmd=f"{CMD_RELATIVE} badcommand"
        )

    def test_verify(self):
        self.assertRaises(
            PersistentStorageException, run_command, cmd=f"{CMD_RELATIVE} verify"
        )


class Apply(unittest.TestCase):
    def setUp(self) -> None:
        run_command(cmd=f"{CMD_RELATIVE} clean", fail=False)

    def tearDown(self) -> None:
        run_command(cmd=f"{CMD_RELATIVE} clean", fail=False)

    def test_apply(self):
        run_command(cmd=f"{CMD_RELATIVE} apply")

    def test_verify(self):
        self.test_apply()
        run_command(cmd=f"{CMD_RELATIVE} verify")

    def test_clean(self):
        self.test_verify()
        run_command(cmd=f"{CMD_RELATIVE} clean")


class NormalUser(unittest.TestCase):
    test_command = f"python3 {DATA_DIR}/e2e_test.py"

    def setUp(self) -> None:
        run_command(cmd=f"{CMD_RELATIVE} clean", fail=False)
        run_command(cmd=f"{CMD_RELATIVE} apply")
        self.storage_file = os.path.join(tempfile.mktemp(), "storage_e2e.yaml")

    def tearDown(self) -> None:
        run_command(cmd=f"{CMD_RELATIVE} clean", fail=False)
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        tmpdir = os.path.join("/tmp", os.path.basename(self.storage_file))
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)

    def testWithoutSupport(self):
        output = run_command(cmd=self.test_command, output=True)
        self.assertIn("/tmp/tmp", output)
        self.assertNotIn("static_tmp_1", output)
        self.assertNotIn("storage_e2e", output)

    def testSupport(self):
        envs = (
            f"{ENV_STORAGE_FILE}={self.storage_file}"
            f" {ENV_REPLACEMENT_FILE}={DATA_DIR}/e2e_test_replacements.py"
        )
        cmd = f"""bash -c '{envs} {self.test_command}'"""
        output = run_command(cmd=cmd, output=True)
        self.assertIn("static_tmp_1", output)
        self.assertIn("storage_e2e", output)


@unittest.skipUnless(
    is_sudo_possible(), "not possible to run, unless you are root or have sudo"
)
class SuperUser(NormalUser):
    test_command = f"python3 {DATA_DIR}/e2e_test.py"

    def setUp(self) -> None:
        run_command(cmd=f"sudo {CMD_RELATIVE} --system clean", fail=False)
        run_command(cmd=f"sudo {CMD_RELATIVE} --system apply")
        self.storage_file = os.path.join(tempfile.mktemp(), "storage_e2e.yaml")

    def tearDown(self) -> None:
        run_command(cmd=f"sudo {CMD_RELATIVE} --system clean", fail=False)
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        tmpdir = os.path.join("/tmp", os.path.basename(self.storage_file))
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)

    def test_installation_path(self):
        output = run_command(cmd=f"{CMD_RELATIVE} --system verify", output=True)
        self.assertIn("Python patched", output)
        self.assertIn("/usr/lib/python", output)


class Latency(unittest.TestCase):
    test_command = f"python3 {DATA_DIR}/e2e_latency_test.py"

    def setUp(self) -> None:
        run_command(cmd=f"{CMD_RELATIVE} clean", fail=False)
        run_command(cmd=f"{CMD_RELATIVE} apply")
        self.storage_file = tempfile.mktemp()

    def tearDown(self) -> None:
        run_command(cmd=f"{CMD_RELATIVE} clean", fail=False)
        os.remove(self.storage_file)

    def check(self, replacements, apply_latency, latency, delta):
        """
        Check if it is really waiting for function call, when latency is enabled
        """
        envs = (
            f"{ENV_STORAGE_FILE}={self.storage_file} "
            f"{ENV_REPLACEMENT_FILE}={DATA_DIR}/{replacements} "
            f"{ENV_APPLY_LATENCY}={apply_latency}"
        )
        cmd = f"""bash -c '{envs} {self.test_command}'"""
        print(cmd)
        self.assertFalse(os.path.exists(self.storage_file))
        before = time.time()
        run_command(cmd=cmd, output=True)
        after = time.time()
        print(open(self.storage_file).readlines())
        self.assertTrue(os.path.exists(self.storage_file))

        self.assertAlmostEqual(2, after - before, delta=delta)
        before = time.time()
        run_command(cmd=cmd, output=True)
        after = time.time()
        self.assertAlmostEqual(latency, after - before, delta=delta)

    def test_not_enabled(self):
        self.check("e2e_latency_replacements.py", "", 0, 1)

    def test_enabled_plain(self):
        self.check("e2e_latency_replacements.py", "YES", 2, 1)


class ReplacementVariable(unittest.TestCase):
    test_command = f"python3 {DATA_DIR}/e2e_test.py"

    def setUp(self) -> None:
        run_command(cmd=f"{CMD_RELATIVE} clean", fail=False)
        run_command(cmd=f"{CMD_RELATIVE} apply")
        self.storage_file = os.path.join(tempfile.mktemp(), "storage_e2e.yaml")

    def tearDown(self) -> None:
        run_command(cmd=f"{CMD_RELATIVE} clean", fail=False)
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        tmpdir = os.path.join("/tmp", os.path.basename(self.storage_file))
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)

    def testSupport(self):
        envs = (
            f"{ENV_STORAGE_FILE}={self.storage_file}"
            f" {ENV_REPLACEMENT_FILE}={DATA_DIR}/e2e_test_replacements_special.py"
            f" {ENV_REPLACEMENT_NAME}=special"
        )
        cmd = f"""bash -c '{envs} {self.test_command}'"""
        output = run_command(cmd=cmd, output=True)
        self.assertIn("static_tmp_1", output)
        self.assertIn("storage_e2e", output)

    def testException(self):
        envs = (
            f"{ENV_STORAGE_FILE}={self.storage_file}"
            f" {ENV_REPLACEMENT_FILE}={DATA_DIR}/e2e_test_replacements_special.py"
            f" {ENV_REPLACEMENT_NAME}=nonsense"
        )
        cmd = f"""bash -c '{envs} {self.test_command}'"""
        self.assertRaises(PersistentStorageException, run_command, cmd=cmd, output=True)

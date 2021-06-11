# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from requre.import_system import UpgradeImportSystem
from requre.helpers.tempfile import TempFile

FILTERS = UpgradeImportSystem().decorate(
    what="tempfile.mktemp", decorator=TempFile.mktemp()
)

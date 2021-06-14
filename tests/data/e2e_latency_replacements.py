# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from requre.import_system import UpgradeImportSystem
from requre.simple_object import Simple

FILTERS = UpgradeImportSystem().decorate("time.sleep", Simple.decorator_plain())

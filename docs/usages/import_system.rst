Import system
-------------

Transparent replacements
________________________

When ``requre`` is installed. It allows call python code
with environment variables what set requre replacements
system and storage file.

- RESPONSE_FILE
    Storage file path for session recording.
    In case file does not exists, it will use write mode
    In case file exists, it will use read mode for Storage
- REPLACEMENT_FILE
    Replacement file path for import system.
    It is important to have there set variable ``FILTERS`` what will
    be used as replacements list for upgrade_import_system function.
    For more information what ``FILTERS`` variable should contain is described in `Filter format`_.
- REPLACEMENT_VAR
    Overrides default value of variable in REPLACEMENT_FILE
    what will be used as replacement variable.
- DEBUG
    if set, print debugging information, fi requre is applied
- LATENCY
    Apply latency waits for test, to have similar test timing
    It is important when using some async/messaging calls

.. _Filter format: ../filter_format.html

Requested replacements
______________________

This is an explicit way of how to use requre in your project.
The best way how to use it in your integration tests.
You have full control of PersistentStorage and you have
store whatever you want.

Paste ``requre`` import update code as ``__init__.py`` in your eg. ``pytest`` tests
Example in `Filter format ogr example`_.

.. _Filter format ogr example: ../filter_format.html#full-example-in-ogr-project

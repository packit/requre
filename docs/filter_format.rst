Filters
=======


Plain
-----
Filter is based representation of the mechanism of
replacing modules, functions or decorating functions.
It is a list of tuples or triples.

eg.

.. code-block:: python

    [
        (
            "^requests$",
            {"who_name": "your_module"},
            {
                "Session.send": [
                    ReplaceType.DECORATOR,
                    RequestResponseHandling.decorator(item_list=[]),
                ]
            }
        ),
    ...
    ]

Import name
___________
``"^requests$"``

It is used to say which module will be replaced in this case
``requests`` module. It uses regular expression syntax, to help
you to use various magic with name search.

Additional filters
___________________________________________________
``{"who_name": "your_module"}``

Is ``dict`` of various stored values, what can be used as additional
filters.

- ``who``
    Module object which imports the selected module (It is most generic,
    but you should use it very carefully)
- ``who_name``
    Name of the module which imports the selected module.
    This is the best option of how to use additional filters.
    It also allows to use regular expressions
- ``who_filename``
    File path to module which imports the selected module
- ``module_object``
    Module object what will be imported. Use it carefully.
    Could be used for modification when there is no support
    in ``requre`` project
- ``fromlist``
    List of names when there is used syntax ``from module import something``

Customization rules
___________________
.. code-block:: python

    {
        "Session.send": [
            ReplaceType.DECORATOR,
            RequestResponseHandling.decorator(item_list=[]),
        ]
    }

It is the most complex part of this triple. It allows to say:

- What to replace
- Which method of replacements to use
- What will replaces/decorates it

Could be also empty. Useful in case using logging to file.
It could help you to find which modules are imported by which ones.

- What to replace: ``Session.send``
    There is used ``"."`` syntax to deep dive into object/module model. In this example, it means in full sense decorate ``send``
    method of ``Session`` class in ``requests`` module
- Types of replacements: ``ReplaceType.DECORATOR``
    Type of how to handle the last parameter, how to apply it to the selected object. They are defined in ``ReplaceType`` class in ``requre/import_system.py`` file

    - DECORATOR
        Decorate original function.
        As **what** it will decorate the original object. Decorators should be
        children of base object class in ``requre/objects.py``.
        And requre defines some useful for you in ``requre/helpers`` directory
    - REPLACE
        Replace object by another one. Typically you can replace
        original implementation by your own, (eg. ``lambda x: print(x)``
        what will replace the original function by new definition
    - REPLACE_MODULE
        Replace the whole module by another implementation. It replaces whole
        module by another one (eg. ``requre`` implements tempfile  module as
        class in helpers to avoid random names for calls
- Object to be used: ``RequestResponseHandling.decorator(item_list=[])``
    It is function/object/method to be applied as ``ReplacementType``.

Filter object model
-------------------
It is wrapper for Plain format, and allows to write it via objects,
instead of writing complex structures.
This have various features described bellow

Replacements
____________
There are three functions/methods that can be used
 - decorate
 - replace
 - replace_module

Example with ``module_replace``

.. code-block:: python

    with replace_module(
        where="^tempfile$", what=TempFile, who_name=SELECTOR
    ):
        import tempfile
        tmpfile = tempfile.mktemp()

Reverting
_________
Requre supports reverting import system to previous state,
when used with ``with`` statement

- Without reverting
    Usage without reverting back

.. code-block:: python

    replace_module(
        where="^tempfile$", what=TempFile, who_name=SELECTOR
    )

    import tempfile
    tmpfile = tempfile.mktemp()

- With reverting
    when used ``with`` statement import system is returned to previous state

.. code-block:: python

    with replace_module(
        where="^tempfile$", what=TempFile, who_name=SELECTOR
    ):
        import tempfile
        tmpfile = tempfile.mktemp()

Chaining of operations
______________________

.. code-block:: python

    with replace_module(where="^tempfile$", what=TempFile, who_name=SELECTOR).replace_module(
        where="^tempfile2$", what=TempFile2, who_name=SELECTOR
    ):
        import tempfile
        tmpfile = tempfile.mktemp()

The real replacement is done in the function/method call -
if we want to postpone the replacement, we need a little bit
different syntax (trigger in the end):

.. code-block:: python

    with add_replace_module(where="^tempfile$", what=TempFile, who_name=SELECTOR).add_replace_module(
        where="^tempfile2$", what=TempFile2, who_name=SELECTOR
    ).upgrade():
        import tempfile
        tmpfile = tempfile.mktemp()

Example in packit project
_________________________

.. code-block:: python

    upgrade_import_system(debug_file="modules.out").decorate(
        where="download_helper",
        what="DownloadHelper.request",
        who_name="lookaside_cache_helper",
        decorator=RequestResponseHandling.decorator_plain,
    ).decorate(
        where="^requests$",
        who_name=["lookaside_cache_helper", "^copr", "packit.distgit"],
        what="Session.send",
        decorator=RequestResponseHandling.decorator(item_list=[]),
    ).replace_module(
        where="^tempfile$", who_name="^packit", what=TempFile
    ).decorate(
        where="^packit$",
        who_name="fedpkg",
        what="utils.run_command_remote",
        decorator=store_function_output,
    ).decorate(
        where="fedpkg",
        what="FedPKG.clone",
        decorator=StoreFiles.arg_references(files_params={"target_path": 2}),
    ).decorate(
        where="git",
        who_name="local_project",
        what="remote.Remote.push",
        decorator=PushInfoStorageList.decorator(item_list=[]),
    )

Full example in ogr project
___________________________
See example in `Ogr project`_ how to use it.
Paste ``requre`` code as ``__init__.py`` in your eg. ``pytest`` tests

.. _Ogr project: https://github.com/packit-service/ogr/blob/master/tests/integration/__init__.py

.. code-block:: python

    from requre.helpers.requests_response import RequestResponseHandling
    from requre.import_system import upgrade_import_system

    ogr_import_system = (
        upgrade_import_system(debug_file="modules.out")
        .log_imports(what="^requests$", who_name=["ogr", "gitlab", "github"])
        .decorate(
            where="^requests$",
            what="Session.send",
            who_name=[
                "ogr.services.pagure",
                "gitlab",
                "github.MainClass",
                "github.Requester",
                "ogr.services.github_tweak",
            ],
            decorator=RequestResponseHandling.decorator(item_list=[]),
        )
    )

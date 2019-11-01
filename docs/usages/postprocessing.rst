Storage File postprocessing
---------------------------

Requre allows you to filter generated data files for sensitive values
what is changed every time, eg. timestamps.

This feature is important to git or public repositories
 - avoid unwanted changes
 - leaking sensitive data

There are two possibilities for how to use it:
 - Command-line tool - simple usage, apply rules to files, but not so powerful.
 - Directly in python - You have to call the ``DictProcessing`` object from ``requre.utils``
   It is more powerful because you avoid relying on some retyping of command line
   parameters

Command line tool
_________________
It Applies replacements rules to files.
Replacements rule format is described with the help of the command-line tool.

The format is ``match_string:key:type_of_value:value``
 - ``match_string`` use format ``selector1%selector2%...`` to select subtrees where to apply rules. It can be also omitted, then replacement is applied to the whole tree.
 - ``key`` - name of ``key`` where ``value`` will be replaced. It supports replacing just dictionary items, but on any level.
 - ``value`` - value to replace in ``key`` item.

.. code-block:: bash

    $ requre-patch purge --help
    Usage: requre-patch purge [OPTIONS] [FILES]...

    Options:
      --replaces TEXT  match_string:key:type_of_value:value = Substitution query
                       in format, where match_string is in format of selecting
                       dictionary keys:selector1%selector2, type_of_value is some
                       object what is serializable and part or builtins module
                       (e.g. int)
      --dry-run        Do not write changes back
      --help           Show this message and exit.



Usage inside python code
________________________

You can play with replaces when you have access to python code and to ``STORAGE`` object.

Example usage could be, that your test code, does data postprocessing as part
of **tear down** steps of test code, before persistent storage is explicitly dumped.

.. code-block:: bash

    from requre.utils import STORAGE, DictProcessing

    class testClass(unittest.TestCase):
        def setUp(self):
            STORAGE.storage_file = "/tmp/file.yaml"

        def teadDown(self):
            dp = DictProcessing(STORAGE.object_storage)
            matched_subdict = dp.match(["a", "b", 1])
            dp.replace(matched_subdict, "key", "value")
            STOTAGE.dump()

        def test(self):
            # any code using replacement

Exmplanation of example:
 - ``dp = DictProcessing(STORAGE.object_storage)``
      Pass storage dict (``STORAGE.object_storage``) object to processing class
 - ``matched_subdict = dp.match(["a", "b", 1])``
      Use keys ``"a", "b", 1`` for searching in dictionary keys. There is important
      order, but not mandatory to be direct children.
 - ``dp.replace(matched_subdict, "key", "value")``
      Replace every occurrence of key-value by ``"value"`` (It searches it in dictionaries)

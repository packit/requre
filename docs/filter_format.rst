Recording decorators & Filter formats
=====================================
There are two types of decorators, **be aware** to not mix these.

 - **Decorators for modification of loaded libraries** - These decorators are in online_replacing and  modules_decorate_all_methods files.
    - Shortcut of decorators for some sets applicable to the whole class.
    - Class decorators - Apply replacements decorators to all methods.
    - Method decorators - Apply replacements decorators to the method.
 - **Replacement decorators wokflow** - These decorators are part of helpers subdirectory and objects file where is the base class with main implementation.
    - Decorators for functions what should be modified (basic unit for working with object storage)

Class decorators
---------------------
There are shortcuts for decorating the whole class by decorators for tests methods.
You can define also setup and teardown methods for cassette as callback methods:

 - ``cassette_setup(self, cassette)`` - Setup cassette before test execution. It is executed after ``self.setUp`` method of unittest.
 - ``cassette_teardown(self, cassette)`` - Tear down method for cassette after test execution. It is executed before ``self.tearDown`` method of unittest.


Generic usage
_______________________
It applies selected decorator to all methods of class. Structure is:

 - **class decorator** - apply_decorator_to_all_methods - Applies argument to all test methods  (``test.*``).
 - **type of matching** - replace_module_match - Decorates already loaded modules via modify of ``sys.modules``
 - **what will be decorated** - ``math.sin`` - Which module method will be decorated.
 - **decorated by** - ``Simple.decorator_plain()`` - This is the decorator for selected method in module.

.. code-block:: python

    @apply_decorator_to_all_methods(
       replace_module_match(
           what="math.sin", decorate=Simple.decorator_plain()
       )
    )

Shortcuts for selected modules
______________________________
The most user-friendly way how to work with requre, but just some modules or their parts are handled by these
(focused on usage requre in packit projects).

They are stored in ``requre/modules_decorate_all_methods.py`` file.

 - **record_tempfile_module** -  Workaround random file names via tempfile module. It changes it to use predictable names.
 - **record_git_module** - The git module handling, it allows to restore remote git operations like fetch, push, pull.
 - **record_requests_module** - Store all remote operations via requests module, it changes ``requests.Session.send`` method, so it should be very generic.


Test methods decorators
-----------------------
These decorators apply a decorator to the test method.

.. code-block:: python

    class Test(unittest.TestCase):

       @replace_module_match(
           what="requests.sessions.Session.request",
           decorate=RequestResponseHandling.decorator(item_list=["method", "url"]),
       )
       def test(self):
           response = requests.get("http://example.com")
           self.assertIn("This domain is for use", response.text)


Filters for transparent mode
----------------------------
This filters are used for transparent mode as part of improved import system,
also deprecated usage for normal tests. The file could look like:

.. code-block:: python

    from requre.import_system import UpgradeImportSystem
    from requre.helpers.simple_object import Simple

    FILTERS = UpgradeImportSystem().decorate("time.sleep", Simple.decorator_plain())


Customization rules
___________________
.. code-block:: python

    from requre import decorate
    from requre.helpers.requests import RequestResponseHandling
    decorate("Session.send", RequestResponseHandling.decorator_plain())


It says

- What to replace
- Which decorator/replacements to use for the method

- What to replace: ``Session.send``
    There is used ``"."`` syntax to deep dive into object/module model. In this example, it means in full sense decorate ``send``
    method of ``Session`` class in ``requests`` module
- Object to be used: ``RequestResponseHandling.decorator_plain()``
    It is function/object/method to be applied as decorator for ``Session.send``.

Filter object model
-------------------

Replacements
____________
There are two functions/methods that can be used
 - decorate
 - replace

Example with ``replace``

.. code-block:: python

    with replace(what="tempfile.mktemp", replacement=lambda x: lambda: "/tmp/random"):
        import tempfile
        tmpfile = tempfile.mktemp()
        assert "/tmp/random" == tmpfile

Reverting
_________
Requre supports reverting import system to previous state,
when used with ``with`` statement

- Without reverting
    Usage without reverting back

.. code-block:: python

    replace(what="tempfile.mktemp", replacement=lambda x: "/tmp/random")
    import tempfile
    tmpfile = tempfile.mktemp()

- With reverting
    when used ``with`` statement import system is returned to previous state

.. code-block:: python

    with replace(what="tempfile.mktemp", replacement=lambda x: "/tmp/random"):
        import tempfile
        tmpfile = tempfile.mktemp()
        assert "/tmp/random" == tmpfile

Chaining of operations
______________________

.. code-block:: python

    with replace(what="tempfile.mktemp", replacement=lambda x: "/tmp/random").\
        decorate(what="tempfile.mkdtemp", replacement=lambda x: lambda: os.makedirs("/tmp/randomdir"))
    ):
        import tempfile
        tmpfile = tempfile.mktemp()
        tempdir = tempfile.mkdtemp()

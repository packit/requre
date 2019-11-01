Storage Helpers
---------------
All storage helpers should be inherited of basic object class
implementing useful decorators.

Methods to use:
 - ``decorator(item_list: list)``
     Allows to use specific positional or keyword arguments as additional
     keys in storage.
     Ensure that the code uses it consistently (must not mix same positional
     and key-value paramters) (e.g. ``decorator(item_list=[1, "data"]``,
     it means use first positional parameter  and ``data`` parameter as keys).
     Why do not use the ``0`` parameter. in object method model ``0`` parameter
     is ``self or cls``, that's why ``1`` as the first parameter
 - ``decorator_plain``
     Use Just base keys, no additional keys for storage
 - ``decorator_all_keys``
     Use all key and positional arguments as additional keys in storage.

Base Object class
_________________
``object.ObjectStorage``

The most generic storage class. It uses pickle as de/serialize function,
so that it allows you to store any pickleable objects.

There is more lowlights why to not use it directly:
 - Data are not nicely represented in YAML file
 - You can leak some unwanted information - eg. when some request object
   is part of a response object and in request object, there are stored all
   auth headers.

Simple Object class
___________________
``requre.helpers.simple_object.Simple``

Storage class for directly YAML serializable objects
e.g. ``string``, ``number``, ``boolean``, ``list``, ``dict``
or a combination of these objects.


Module requests -  Response handling
____________________________________
``requre.helpers.requests_response.RequestResponseHandling``

It handles ``Response`` of ``requests`` module for various modules.
The most generic is to decorate ``requests.Session.send`` that is the most
low level.

Module git PushInfo handling
____________________________
``requre.helpers.git.pushinfo.PushInfoStorageList``

It stores information about Pushes to git.


File and directory handling
---------------------------
``requre.helpers.files.StoreFiles``
This allows you to use decorators to store files or directories
to persistent storage. It allows to use several decorators, how
and what to store.

 - ``return_value``
    It uses return value  of method/function as name of file or directory and store
 - ``guess_args``
    Try to guess which parameter of function is file. It is based on the existence of the argument on the filesystem. It checks every ``string`` argument
 - ``arg_references(files_params: Dict)``
    Exact reference which argument is file. ``files_params`` dictionary contains a definition
    of pairs, ``named_value: int_position`` of argument to be able to handle
    key-value parameters and positional as well.

Tempfile handling
-----------------
``requre.helpers.tempfile.TempFile``

replacement for python  ``tempfile`` module by this implementation.
Reason why is, that you would like to avoid to have random names as arguments of functions.
Or you would like to have all generated files in one separate place, to see what happens inside.
Instead of some generic /tmp/tmp* dirs or files.

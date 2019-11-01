Installation
============

Github master
----------------
1. Download sources code

.. code-block:: bash

   git clone https://github.com/packit-service/requre.git

2. Install (important to use ``sudo`` to install requre binaries  )

.. code-block:: bash

   cd requre
   sudo pip3 install .


Requre as transparent tool
----------------------------------

You can use requre as transparent tool for your **Functional** or
**E2E** testing. In case you would like to do, you have to install
a handler to your python interpreter.

.. code-block:: bash

    $ requre-patch
    Usage: requre-patch [OPTIONS] COMMAND [ARGS]...

    Options:
      --version TEXT  Version of python to patch
      --system        Use system python path, instead of user home dir
      --help          Show this message and exit.

    Commands:
      apply
      clean
      purge
      verify

You can import it to your user's or system python to ``site-packages``

.. code-block:: bash

    $ requre-patch apply
    Applying import patch to python (file: /home/user/.local/lib/python3.7/site-packages/sitecustomize.py)

To use it in a transparent way see: `Transparent Usage`_.

.. _Transparent Usage: usages/import_system.html#transparent-replacements

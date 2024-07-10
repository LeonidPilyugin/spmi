Getting started
===============

.. warning::

   This project is under active development.

.. todo::

    * Update this section.
    * See API TODOs
    * Make ``Pool`` to lock and release ``Manageable`` metadata.

What is SPMI
------------
SPMI (Simple Process Manager Interface) is a Python package which provides an
application and library to start processes via different process managers
(e.g. `GNU Screen <https://www.gnu.org/software/screen/>`_ and `SLURM <https://slurm.schedmd.com/overview.html>`_). It works only in UNIX-like systems.

Installation
------------

Clone git repository:

.. code-block:: console

    $ git clone https://github.com/LeonidPilyugin/spmi
    $ cd spmi

Install dependencies:

.. code-block:: console

    $ pip install -r requirements.txt

Basic usage
-----------
The core object of SPMI is ``Manageable``.
It describes process which can be managed by SPMI.
``spmi.core.manageables`` contains realisations of
``Manageable``. For example, ``TaskManageable`` is a
``Manageable`` which runs a single command via specific
``TaskManageable.Backend``. ``TaskManageable.Backend`` is
an interface to process manager (``ScreenBackend`` is an interface to GNU Screen).

Before starting ``Manageable``, create its descriptor file.
SPMI supports several file formats and detects format based on file extention.

Create a simple task descriptor ``task.toml``:

.. code-block:: TOML

    [task]                  # type of manageable
    id = "toml_task"        # ID of manageable

    [task.backend]          # backend section
    type = "screen"         # type of backend

    [task.wrapper]          # wrapper section
    type = "default"        # type of wrapper
    command = "sleep 10"    # command to execute

Be sure that `GNU Screen <https://www.gnu.org/software/screen/>`_ is installed.

Then, start a new task:

.. code-block:: console

    $ spmi list
    detected: "example_task" by path "task.toml"

.. code-block:: console

    $ spmi start example_task
    started: "example_task"

.. code-block:: console

    $ spmi list
    detected: "example_task" by path "/path/to/task.toml"
    registered: "example_task"

.. code-block:: console

    $ spmi status example_task

.. code-block:: console

    $ spmi stop example_task

.. code-block:: console

    $ spmi status example_task

.. code-block:: console

    $ spmi list

.. code-block:: console

    $ spmi clean example_task

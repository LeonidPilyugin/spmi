Getting started
===============

.. warning::

   This project is under active development.

.. todo::

    * Update this section.
    * See API TODOs
    * Update ``requirements.txt``

What is SPMI
------------
SPMI (Simple Process Manager Interface) is a Python package which provides an
application and library to start processes via different process managers
(e.g. `GNU screen <https://www.gnu.org/software/screen/>`_ and `SLURM <https://slurm.schedmd.com/overview.html>`_).

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
The core object of SPMI is :class:`spmi.core.manageable.Manageable`.
It describes process which can be managed by SPMI.
:py:mod:`spmi.core.manageables` contains realisations of
:class:`Manageable`.
For example, :class:`spmi.core.manageables.task.TaskManageable` is a
:class:`Manageable`
which runs a single command via specific
:class:`TaskManageable.Backend`. :class:`TaskManageable.Backend` is
an interface to process manager (:class:`spmi.core.manageables.task_.backend.screen.ScreenBackend` is an interface to GNU Screen).

Before starting :class:`Manageable`, create its descriptor file.
SPMI supports several file formats and detects format based on file extention.

Create a simple task descriptor:

.. code-block:: JSON

    {
        "task": {                       // type of manageable to start
            "id": "example_task",       // ID of manageable
            "backend": {                // backend section
                "type": "screen"        // type of backend
            },
            "wrapper": {                // wrapper section
                "type": "default",      // type of wrapper
                "command": "sleep 10"   // command to execute
            }
        }
    }


Then, start a new task:

.. code-block:: console

    $ spmi list
    detected: "example_task" by path "path/to/your/task.json"

.. code-block:: console

    $ spmi start example_task
    started: "example_task"

.. code-block:: console

    $ spmi list
    detected: "example_task" by path "path/to/your/task.json"
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

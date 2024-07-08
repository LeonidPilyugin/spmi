Getting started
===============

.. note::

   This project is under active development.

.. todo:: Create aliases for classes in documentation.

What is SPMI
------------
SPMI (Simple Process Manager Interface) is a Python package which provides an
application and library to start processes via different process managers
(e.g. `GNU screen <https://www.gnu.org/software/screen/>`_ and `SLURM <https://slurm.schedmd.com/overview.html>`_).

Installation
------------

First, clone git repository:

.. code-block:: console

    $ git clone https://github.com/LeonidPilyugin/spmi
    $ cd spmi

Then, create a virtual python environment:

.. code-block:: console

    $ python -m venv .venv

Install dependencies:

.. code-block:: console

    (.venv) $ pip install -r requirements.txt

Basic usage
-----------
The core object of SPMI is :class:`spmi.core.manageable.Manageable`.
It describes process which can be managed by SPMI.
:py:mod:`spmi.core.manageables` contains realisations of
:class:`spmi.core.manageable.Manageable`.
For example, :class:`spmi.core.manageables.task.TaskManageable` is a
:class:`spmi.core.manageable.Manageable`
which runs a single command via specific
:class:`spmi.core.manageables.task.TaskManageable.Backend`.


.. todo:: Write about manageable structure.

Each :class:`spmi.core.manageable.Manageable` has a :py:attr:`spmi.core.manageable.Manageable.state` property which

JSON descriptor example:

.. code-block:: JSON

    {
        "task": {
            "id": "json_task",
            "backend": {
                "type": "screen"
            },
            "wrapper": {
                "type": "default",
                "command": "sleep 10"
            }
        }
    }


Also it in TOML:

.. code-block:: TOML

    [task]
    id = "toml_task"

    [task.backend]
    type = "screen"

    [task.wrapper]
    type = "default"
    command = "sleep 10"





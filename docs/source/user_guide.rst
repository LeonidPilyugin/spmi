User guide
==========

.. _descriptor-section-label:

Data model
----------

SPMI operates on objects, called "manageables".
Abstract class :class:`spmi.core.manageable.Manageable` describes them.

Each manageable may be in 3 states:

* Untracked. Manageable has a created a descriptor, but isn't loaded to SPMI.

* Inactive. Manageable loaded to SPMI but hasn't running processes.

* Active. Manageable loaded to SPMI and has running process.

.. note:: Manageables are placed in their modules in :mod:`spmi.core.manageables` package.
    Each realisation of :class:`spmi.core.manageable.Manageable` must be its child and decorated with :func:`spmi.core.manageable.manageable`. Its name must end with ``Manageable``.

.. note:: In this version the only realisation of manageable is task (:class:`spmi.core.manageables.task.TaskManageable`).

Task manageable handles a single shell command.
It has associated :class:`spmi.core.manageables.task.TaskManageable.Backend`
and :class:`spmi.core.manageables.task.TaskManageable.Wrapper` objects.
backend is an interface to process manager and wrapper manages
command execution (e.g. handles signals).

.. note:: Backends are placed in their modules in :mod:`spmi.core.manageables.task_.backends` package. Each realisation of :class:`spmi.core.manageables.task.TaskManageable.Backend` must be its child. Its name must end with ``Backend``.

.. note:: In this version the only realisation of backend is :class:`spmi.core.manageables.task_.backends.screen.ScreenBackend`.

.. note:: Wrappers are placed in their modules in :mod:`spmi.core.manageables.task_.wrappers` package. Each realisation of :class:`spmi.core.manageables.task.TaskManageable.Wrapper` must be its child. Its name must end with ``Wrapper``.

.. note:: In this version the only realisation of wrapper is :class:`spmi.core.manageables.task_.wrappers.default.DefaultWrapper`.


Descriptor
----------

Descriptor is a file which contains information which SPMI needs
to start manageable.
SPMI supports TOML, YAML and JSON descriptors.
Next I will write about manageable descriptor in TOML format.
Other formats must represent the same structure.

Descriptor begins with ``[task]`` table. It tells SPMI the type
of manageable. ``[task]`` corresponds
:class:`spmi.core.manageables.task.TaskManageable` class.
If you write ``[some_manageable_realisation]`` instead of ``[task]``,
SPMI will search for ``SomeManageableRealisationManageable`` class inside
one module of :mod:`spmi.core.manageables` package.

In this table you can see fields ``id`` and ``comment``.
``id`` is an identificator for manageable, ``comment``
is its description.

For task, there are two subtables: ``[task.backend]`` and
``[task.wrapper]``. ``[task.backend]`` contains backend
fields, ``[task.wrapper]`` --- wrapper.

Both ``[task.backend]`` and ``[task.wrapper]`` contain a field ``type``.
It describes type of backend or wrapper to use and converts to classname
just like manageable type.

``[task.wrapper]`` also has ``command`` and ``mixed_stdout`` fields.
``command`` is a shell command to start. If ``mixed_stdout`` is ``true``,
SPMI will write stdout and stderr of command to single file.

You can see the same descriptor in different formats below.

.. code-block:: TOML
    :caption: descriptor.toml

    [task]                                      # type of manageable
    id = "cal"                                  # ID of manageable
    comment = "Prints calendar to stdout."      # comment

    [task.backend]                              # backend section
    type = "screen"                             # backend type

    [task.wrapper]                              # wrapper section
    type = "default"                            # type of wrapper
    command = "cal"                             # command to start
    mixed_stdout = true                         # mix stdout and stderr files or not

.. code-block:: YAML
    :caption: descriptor.yaml

    task:
        id: cal
        comment: Prints calendar to stdout.
        backend:
            type: screen
        wrapper:
            type: default
            command: cal
            mixed_stdout: true

.. code-block:: JSON
    :caption: descriptor.json

    {
        "task": {
            "id": "cal",
            "comment": "Prints calendar to stdout.",
            "backend": {
                "type": "screen"
            },
            "wrapper": {
                "type": "default",
                "command": "cal",
                "mixed_stdout": true
            }
        }
    }

`More descriptor examples <https://github.com/LeonidPilyugin/spmi/tree/main/examples>`_.

Usage
-----

Run ``spmi -h`` to view available options:

.. code-block:: console

    $ spmi -h
       _____ ____  __  _______
      / ___// __ \/  |/  /  _/
      \__ \/ /_/ / /|_/ // /
     ___/ / ____/ /  / // /
    /____/_/   /_/  /_/___/

    Simple Process Management Interface

    SPMI is a program to maintain processes.

    Usage:
        spmi list [-d | --debug]
        spmi load <pathes>... [-d | --debug]
        spmi start <patterns>... [-d | --debug]
        spmi stop <patterns>... [-d | --debug]
        spmi kill <patterns>... [-d | --debug]
        spmi clean <patterns>... [-d | --debug]
        spmi status <patterns>... [-d | --debug]
        spmi connect <task_id> [-d | --debug]

    Options:
        -h --help       Show this screen
        -v --version    Show version
        -d --debug      Run in debug mode

.. note:: SPMI uses regex to match ID patterns.

Load
~~~~

If you have a manageable descriptor file
``decriptor.toml``, you can load
it using ``spmi load``:

.. code-block:: console

    $ spmi load descriptor.toml
    [2024-07-14 19:17:17,231 - Spmi - INFO]
    Loaded 1 manageable

You can also load many manageables with single command:

.. code-block:: console

    $ spmi load descriptor1.toml descriptor2.toml descriptor3.toml
    [2024-07-14 19:18:46,205 - Spmi - INFO]
    Loaded 3 manageables

.. note:: SPMI stores loaded manageables in ``$SPMI_PATH`` directory
    (the default value is ``~/.spmi``).

List
~~~~

You can see list of loaded manageables with ``spmi list``:

.. code-block:: console

    $ spmi list
    [2024-07-14 19:21:29,465 - Spmi - INFO]
    Registered 3 manageables
    ID           ACTIVE    COMMENT
    manageable_2 inactive  Comment 2
    manageable_1 inactive  Comment 1
    manageable_3 inactive  Comment 3

Start
~~~~~

To start task, run ``spmi run <task_id>``:

.. code-block:: console

    $ spmi start manageable_1
    [2024-07-14 19:27:03,560 - Spmi - INFO]
    Starting manageable "manageable_1"
    [2024-07-14 19:27:03,567 - Spmi - INFO]
    Started 1 manageables

SPMI matches ID based on regex. You can start ``manageable_1``,
``manageable_2`` and ``manageable_3`` with

.. code-block:: console

    $ spmi start 'manageable_[1-3]'
    [2024-07-14 19:29:04,848 - Spmi - INFO]
    Starting manageable "manageable_2"
    [2024-07-14 19:29:04,856 - Spmi - INFO]
    Starting manageable "manageable_1"
    [2024-07-14 19:29:04,865 - Spmi - INFO]
    Starting manageable "manageable_3"
    [2024-07-14 19:29:04,873 - Spmi - INFO]
    Started 3 manageables

.. note:: You cannot start active manageables.

Status
~~~~~~

You can get info about manageable using ``spmi status``:

.. code-block:: console

    $ spmi status manageable_1
    manageable_1 (task) - Comment 1
          Active: inactive since 2024-07-14 19:29:05 (0:00:49 ago)
            Path: "/home/leonid/.spmi/manageable_1"
    Backend type: screen
      Backend ID: 39359
    Wrapper type: default
         Command: echo 1
             PID: 39415
       Exit code: 0

    1

    [2024-07-14 19:29:54,593 - Spmi - INFO]
    Showed 1 manageables

It displays it in format:

.. code-block::

    ID (TYPE) - COMMENT
          Active: (in)active since DATE TIME (DELTA_TIME ago)
            Path: PATH_TO_DIRECTORY
    Backend type: BACKEND_TYPE
      Backend ID: ID_OF_BACKEND_PROCESS
    Wrapper type: WRAPPER_TYPE
         Command: COMMAND
             PID: PID_OF_WRAPPER_TASK
       Exit code: EXIT_CODE

Stop
~~~~

To stop manageable process, use ``spmi stop``:

.. code-block:: console

    $ spmi stop echo
    [2024-07-14 19:40:05,274 - Spmi - INFO]
    Stopping manageable "echo"
    [2024-07-14 19:40:05,281 - Spmi - INFO]
    Stopped 1 manageables

.. note:: You cannot stop inactive manageables.

Kill
~~~~

``spmi kill`` also stops manageable process, but cannot fail
if manageable is active.

.. code-block:: console

    $ spmi kill echo
    [2024-07-14 19:40:29,291 - Spmi - INFO]
    Killing manageable "echo"
    [2024-07-14 19:40:29,298 - Spmi - INFO]
    Killed 1 manageables

.. note:: You cannot kill inactive manageables.

Clean
~~~~~

``spmi clean`` removes manageable from SPMI.

.. code-block:: console

    $ spmi clean echo
    [2024-07-14 19:40:58,336 - Spmi - INFO]
    Cleaning manageable "echo"
    [2024-07-14 19:40:58,341 - Spmi - INFO]
    Cleaned 1 manageables

.. note:: You cannot clean active manageables.

Building documentation
----------------------

Install dependencies

.. code-block:: console

    $ pip install -r build-doc-requirements

Build documentation

.. code-block:: console

    $ cd docs
    $ make html

The HTML documentation will be in ``build`` directory.

Troubleshooting
---------------

If you have troubles with using SPMI, `leave an issue <https://github.com/LeonidPilyugin/spmi/issues>`_

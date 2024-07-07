# SPMI
Simple Process Management Interface

SPMI is a program which provides a systemctl-like interface to start tasks via different backends (GNU screen, SLURM, e.t.c).

# ARCHITECTURE

## Task

Task is a process (or several processes) which was started by SPMI.

It has 4 mods:
1) active       -- process is running
2) finished     -- process is finished itself with exit code 0
3) stopped      -- process was canceled by user via pmi
4) failed       -- process was killed or finished with non-zero exit code

## Group

Group is a plenty of dependend tasks which are unified for one target (e.g. computer simulation pipeline may consist of several processes: simulation and analysis processes).

Group helps to organize processes and handle them: all group may be stopped, restarted, e.t.c.

All actions to tasks/groups in group are applied in order in descriptor file.

## Backend

Backend is an interface to manager which operates submited processes.
Currently supported backends:
1) GNU Screen
2) SLURM

## Wrapper

A script which handles submitted process

## Descriptor

Descriptors are written in JSON.

```
# Single task descriptor example
{
  "id": "Task ID",
  
  "backend": {
    "type": "screen"
  },

  "command": "df -h"

  "log": true,

}
```
```
# Group example
{
  "id": "Group ID",

  "content": [ // list of groups and tasks
    {
      "id", ...
    }, ...
  ]
}

```

## Metadata

After submission a metadata file is assigned to task
This file contains submission time, ...

# USAGE

spmi list-jobs [pattern]
    List all started tasks

spmi is-active/finished/stopped/failed PATTERN
    Returns 0 if any of tasks are active/...

spmi status pattern
    Prints status like systemctl

spmi start PATTERN

spmi stop PATTERN

spmi restart PATTERN

spmi try-restart PATTERN

spmi clean PATTERN

spmi show pattern
    Show config file of task

spmi cat PATTERN
    Show configs of many units

spmi modify pattern
    Modify task config in default editor. Task must not be active

spmi log-level PATTERN level
    Change log level of jobs

spmi help
    Print help message



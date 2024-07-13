# SPMI

Simple Process Management Interface

> [!IMPORTANT]
> This project may be buggy because I haven't tested it enough.

## What is SPMI

SPMI (Simple Process Management Interface) is a Python package which provides
an application and library to start and manage processes via different process
managers (now [GNU Screen](https://www.gnu.org/software/screen/) is supported
and I am going to add [SLURM](https://slurm.schedmd.com/overview.html) support)
for UNIX-like systems.

## Installation

Clone git repository
```sh
$ git clone https://github.com/LeonidPilyugin/spmi
$ cd spmi
```

Switch to version
```sh
$ git checkout v0.0.1
```

Install dependencies
```sh
$ pip install -r requirements.txt
```

Add `spmi/src` to `$PYTHON_PATH` variable and create link to `spmi/src/app.py`
```sh
$ ln -s $PWD/src/spmi/app.py ~/.local/bin/spmi
```

## Basic usage
To start a new process, you need to create a descriptor file. SPMI supports
3 types of descriptor files: JSON, TOML and YAML. There are some examples for
each format in `examples` folder.

Descritor `cal.toml`:
```TOML
[task]
id = "cal"
comment = "Prints calendar to stdout."

[task.backend]
type = "screen"

[task.wrapper]
type = "default"
command = "cal"
mixed_stdout = true
```

View documentation to learn about descriptor structure.

Before starting a new process, ensure that GNU Screen is installed
```sh
$ screen -v
Screen version 4.09.01 (GNU) 20-Aug-23
```

Load descriptor to SPMI
```sh
$ spmi load cal.toml
[2024-07-13 18:21:00,240 - Spmi - INFO]
Loaded 1 manageable
```

View list of tasks
```sh
$ spmi list
[2024-07-13 18:21:55,432 - Spmi - INFO]
Registered 1 manageable
ID        ACTIVE    COMMENT
cal       inactive  Prints calendar to stdout.
```

Start `cal` task
```sh
$ spmi start cal
[2024-07-13 18:24:48,337 - Spmi - INFO]
Starting manageable "cal"
[2024-07-13 18:24:48,344 - Spmi - INFO]
Started 1 manageables
```

And view its status
```sh
$ spmi status cal
cal (task) - Prints calendar to stdout.
      Active: inactive since 2024-07-13 18:24:49 (0:01:03 ago)
        Path: "/home/leonid/.spmi/cal"
Backend type: screen
  Backend ID: 74870
Wrapper type: default
     Command: cal
         PID: 74915
   Exit code: 0

 7  8  9 10 11 12 13
14 15 16 17 18 19 20
21 22 23 24 25 26 27
28 29 30 31


[2024-07-13 18:25:52,255 - Spmi - INFO]
Showed 1 manageables
```

Next, load `ping.toml` example
```sh
$ spmi load ping.toml
[2024-07-13 18:32:20,105 - Spmi - INFO]
Loaded 1 manageable
```

And start it
```sh
$ spmi start ping
[2024-07-13 18:33:12,546 - Spmi - INFO]
Starting manageable "ping"
[2024-07-13 18:33:12,554 - Spmi - INFO]
Started 1 manageables
```

If you do instructions fast, you may see that this task is active
```sh
$ spmi status ping
ping (task) - Pinges localhost 10 times.
      Active: active since 2024-07-13 18:33:12 (0:00:01 ago)
        Path: "/home/leonid/.spmi/ping"
Backend type: screen
  Backend ID: 75810
Wrapper type: default
     Command: ping -c 10 -i 1 localhost
         PID: 75855

PING localhost (::1) 56 data bytes
64 bytes from localhost (::1): icmp_seq=1 ttl=64 time=0.011 ms
64 bytes from localhost (::1): icmp_seq=2 ttl=64 time=0.034 ms

[2024-07-13 18:33:13,794 - Spmi - INFO]
Showed 1 manageables
```

If you don't, start `echo.toml` example
```sh
$ spmi load echo.toml
[2024-07-13 18:36:13,794 - Spmi - INFO]
Loaded 1 manageable
$ spmi start echo
```

And view its status
```sh
$ spmi status echo
echo (task) - A forever echo command.
      Active: active since 2024-07-13 18:36:49 (0:00:44 ago)
        Path: "/home/leonid/.spmi/echo"
Backend type: screen
  Backend ID: 76113
Wrapper type: default
     Command: cat -
         PID: 76158



[2024-07-13 18:37:33,406 - Spmi - INFO]
Showed 1 manageables
```

SPMI allows you to communicate with started process
(but now only write a single line to its stdin)
```sh
$ spmi connect echo
Hello
```

View status again
```sh
$ spmi status echo
echo (task) - A forever echo command.
      Active: active since 2024-07-13 18:36:49 (0:03:46 ago)
        Path: "/home/leonid/.spmi/echo"
Backend type: screen
  Backend ID: 76113
Wrapper type: default
     Command: cat -
         PID: 76158

Hello

[2024-07-13 18:40:35,153 - Spmi - INFO]
Showed 1 manageables
```

`cat -` printed your line to stdout! Next, stop `echo` task

```sh
$ spmi stop echo
[2024-07-13 18:42:04,887 - Spmi - INFO]
Stopping manageable "echo"
[2024-07-13 18:42:04,894 - Spmi - INFO]
Stopped 1 manageables
```

And see its status one more time
```sh
$ spmi status echo
echo (task) - A forever echo command.
      Active: inactive since 2024-07-13 18:42:05 (0:00:54 ago)
        Path: "/home/leonid/.spmi/echo"
Backend type: screen
  Backend ID: 76113
Wrapper type: default
     Command: cat -
         PID: 76158
   Exit code: -2

first

[2024-07-13 18:42:59,899 - Spmi - INFO]
Showed 1 manageables
```

To remove task, you don't want to use, execute `spmi clean`
```sh
$ spmi clean cal
[2024-07-13 18:44:26,503 - Spmi - INFO]
Cleaning manageable "cal"
[2024-07-13 18:44:26,510 - Spmi - INFO]
Cleaned 1 manageables
```

SPMI uses regex to match IDs. To remove all loaded examples, execute
```sh
$ spmi clean ''
[2024-07-13 18:46:38,954 - Spmi - INFO]
Cleaning manageable "ping"
[2024-07-13 18:46:38,962 - Spmi - INFO]
Cleaning manageable "echo"
[2024-07-13 18:46:38,969 - Spmi - INFO]
Cleaned 2 manageables
```

For advanced usage, read SPMI documentation.

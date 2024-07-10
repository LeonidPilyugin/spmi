"""Provides :class:`DefaultWrapper`.
"""

import os
import time
import signal
import shlex
import subprocess
import multiprocessing
from spmi.core.manageables.task import TaskManageable

class DefaultWrapper(TaskManageable.Wrapper):

    def __init__(self, metadata=None):
        super().__init__(metadata=metadata)
        self._to_close = []
        self._to_unlink = []

    def _start_daemon_process(self):
        """Starts a daemon process which prevents EOF of wrapped command."""
        def daemon(exit_event, path):
            fifo_write = os.open(path, os.O_WRONLY)
            while not exit_event.is_set():
                time.sleep(1)
            os.close(fifo_write)

        self._exit_event = multiprocessing.Event()
        self._daemon_process = multiprocessing.Process(
            target=daemon,
            args=(self._exit_event, self._metadata.wrapper.stdin_path),
        )
        self._daemon_process.start()


    def start(self):
        self._logger.info(f"Starting \"{self._metadata.wrapper.command}\" process")

        self._logger.debug("Acquiring metadata")
        self._metadata.acquire()
        self._metadata.load()

        self._logger.debug("Opening stdout on write")
        stdout_path = self._metadata.path.joinpath("process.stdout")
        self._metadata.wrapper.stdout_path = stdout_path
        stdout_path.touch()
        stdout_write = os.open(stdout_path, os.O_WRONLY)
        self._to_close.append(stdout_write)

        if self._metadata.wrapper.mixed_stdout:
            stderr_path = stdout_path
            stderr_write = stdout_write
        else:
            stderr_path = self._metadata.path.joinpath("process.stderr")
            self._metadata.wrapper.stderr_path = stderr_path
            stderr_path.touch()
            self._logger.debug("Opening stderr on write")
            stderr_write = os.open(stderr_path, os.O_WRONLY)
            self._to_close.append(stderr_write)

        stdin_path = self._metadata.path.joinpath("process.stdin")
        self._to_unlink.append(stdin_path)
        self._metadata.wrapper.stdin_path = stdin_path

        self._logger.debug(f"Creating FIFO \"{stdin_path}\"")
        os.mkfifo(stdin_path)

        self._logger.debug("Starting daemon process")
        self._start_daemon_process()

        self._logger.debug("Opening FIFO on read")
        fifo_read = os.open(stdin_path, os.O_RDONLY)
        self._to_close.append(fifo_read)

        self._logger.debug("Starting wrapped process")
        process = subprocess.Popen(
            shlex.split(self._metadata.wrapper.command),
            shell=True,
            stdout=stdout_write,
            stdin=fifo_read,
            stderr=stderr_write,
        )

        self._metadata.wrapper.process_pid = process.pid

        self._logger.debug("Dumping metadata")
        self._metadata.dump()
        self._logger.debug("Releasing metadata")
        self._metadata.release()

        self._logger.info("Waiting wrapped process")
        process.wait()
        self._logger.info("Wrapped process finished")

        self._logger.debug("Finishing daemon process")
        self._exit_event.set()
        self._daemon_process.join()

        self._logger.debug("Acquiring metadata")
        self._metadata.acquire()
        self._logger.debug("Loading metadata")
        self._metadata.load()
        
        self._metadata.wrapper.exit_code = process.returncode
        self._logger.debug("Dumping metadata")
        self._metadata.dump()
        self._logger.debug("Releasing metadata")
        self._metadata.release()


    def on_signal(self, signum, frame):
        self._logger.info(f"Got signal: {signal.Signals(signum).name}")

    def finish(self):
        for f in self._to_close:
            os.close(f)
        for f in self._to_unlink:
            os.unlink(f)




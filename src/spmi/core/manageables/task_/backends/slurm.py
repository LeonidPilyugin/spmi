"""Provides :class:`SlurmBackend`.
"""

import os
import subprocess
from spmi.core.manageables.task import TaskManageable, BackendException
from spmi.utils.logger import Logger

class SlurmBackendException(BackendException):
    pass

class SlurmBackend(TaskManageable.Backend):
    class MetaDataHelper(TaskManageable.Backend.MetaDataHelper):
        @property
        def options(self):
            return list(self._data["options"])

    """SLURM backend."""
    def __init__(self):
        raise NotImplementedError("Now Slurm backend is not implemented")
        self._logger = Logger(self.__class__.__name__)
        self._logger.debug("Creating backend")
        self._job_ids = set()
        self.load_jobs()

    def load_jobs(self):
        """Loads all job IDs."""
        self._logger.debug("Loading IDs of jobs")

        job_ids = [x.strip() for x in subprocess.getoutput("squeue -ho \"%A\"").split("\n")]

        self._job_ids = set(job_ids)

        if len(self._job_ids) != len(job_ids):
            raise SlurmBackendException("Found equal IDs in \"squeue\"")

        self._logger.debug(f"Loaded {len(job_ids)} IDs")

    def _generate_command(self, task_metadata):
        command = "sbatch "
        for option in matedata.backend.options:
            command += f"{option} "
        command += "'{task_metadata.backend.command}'"
        return command

    def submit(self, task_metadata):
        super().submit(task_metadata)
        self._logger.debug("Submitting a new task")

        task_metadata.backend.log_path = task_metadata.path.joinpath("backend.log")

        self.load_jobs()
        old_ids = self._job_ids

        if os.system(self._generate_command(task_metadata)) != 0:
            raise SlurmBackendException("Sbatch failed.")

        self.load_jobs()

        if len(old_ids) + 1 != len(self._job_ids):
            raise SlurmBackendException("New job is not started")

        job_id = list(self._job_ids - old_ids)[0]
        task_metadata.backend.id = job_id

        self._logger.debug(f"New job ID: {screen_id}")

    def term(self, task_metadata):
        super().term(task_metadata)
        if os.system(f"scancel {task_metadata.backend.id}") != 0:
            raise SlurmBackendException(f"Cannot cancel job {task_metadata.backend.id}")

    def kill(self, task_metadata):
        super().kill(task_metadata)
        self.term(task_metadata)

    def is_active(self, task_metadata):
        super().is_active(task_metadata)
        self.load_jobs()
        return task_metadata.backend.id in self._job_ids

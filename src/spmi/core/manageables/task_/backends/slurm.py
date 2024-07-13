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

    def _generate_command(self, metadata):
        command = "sbatch "
        for option in matedata.backend.options:
            command += f"{option} "
        command += "'{metadata.backend.command}'"
        return command

    def submit(self, metadata):
        self._logger.debug("Submitting a new task")

        metadata.backend.log_path = metadata.path.joinpath("backend.log")

        self.load_jobs()
        old_ids = self._job_ids

        if os.system(self._generate_command(metadata)) != 0:
            raise SlurmBackendException("Cannot start screen")

        self.load_jobs()

        if len(old_ids) + 1 != len(self._job_ids):
            raise SlurmBackendException("New job is not started")

        job_id = list(self._job_ids - old_ids)[0]
        metadata.backend.id = job_id

        self._logger.debug(f"New job ID: {screen_id}")

    def term(self, metadata):
        if os.system(f"scancel {metadata.backend.id}") != 0:
            raise SlurmBackendException(f"Cannot cancel job {metadata.backend.id}")

    def kill(self, metadata):
        self.term(metadata)

    def is_active(self, metadata):
        self.load_jobs()
        return metadata.backend.id in self._job_ids

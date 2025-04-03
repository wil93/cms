import logging
import sys
from typing import Optional

from rq import Worker, get_current_job
from rq.job import Job

from cms.grading.Job import BaseJob, CompilationJob
from cms.grading.tasktypes import get_task_type
from cms.db.filecacher import FileCacher, TombstoneError
from cms.service2 import redis_connection
from cms.service2.queues import all_operation_queues

logger = logging.getLogger(__name__)
file_cacher = FileCacher()


def _get_compilation_job() -> Optional[Job]:
    """Get the parent compilation job (i.e. the only dependency) of the current
    evaluation job.

    return (Job): the parent compilation job.

    """
    job = get_current_job()
    if job is None:
        # This can never happen (as long as the function was triggered via RQ)
        return None

    return job.dependency


def process_compilation_job(_compilation_job: dict) -> dict:
    """This function is called by the worker to process a compilation job.

    compilation_job (CompilationJob): the compilation job to process.

    """
    compilation_job = BaseJob.import_from_dict_with_type(_compilation_job)

    logger.info("Starting compilation job.", extra={"operation": compilation_job.info})

    task_type = get_task_type(
        compilation_job.task_type, compilation_job.task_type_parameters
    )
    try:
        task_type.execute_job(compilation_job, file_cacher)
    except TombstoneError:
        compilation_job.success = False
        compilation_job.plus = {"tombstone": True}

    logger.info("Finished job.", extra={"operation": compilation_job.info})

    return compilation_job.export_to_dict()


def process_evaluation_job(_evaluation_job: dict) -> dict:
    """This function is called by the worker to process an evaluation job.

    evaluation_job (EvaluationJob): the evaluation job to process.

    """
    evaluation_job = BaseJob.import_from_dict_with_type(_evaluation_job)

    logger.info("Starting evaluation job.", extra={"operation": evaluation_job.info})

    compilation_job = _get_compilation_job()

    if compilation_job is None:
        # This can happen when:
        #  1) This is a re-evaluation which should re-use the old executable.
        #  2) The evaluation is taking so long (e.g. there are many testcases
        #     with high time limit, or too few workers) that the result of the
        #     compilation job expired its TTL.
        logger.info(
            "No parent compilation job available in the queue, we will "
            "try to fetch the executable file from the storage."
        )
        executables = {}  # TODO: get executables from the database
    else:
        # Standard case: we can still access the result of the compilation job.
        cms_job = BaseJob.import_from_dict_with_type(compilation_job.result)
        assert isinstance(cms_job, CompilationJob)
        executables = cms_job.executables

    # Inject the compiled executables into the evaluation job.
    evaluation_job.executables.update(executables)

    task_type = get_task_type(
        evaluation_job.task_type, evaluation_job.task_type_parameters
    )
    try:
        task_type.execute_job(evaluation_job, file_cacher)
    except TombstoneError:
        evaluation_job.success = False
        evaluation_job.plus = {"tombstone": True}

    logger.info("Finished job.", extra={"operation": evaluation_job.info})

    return evaluation_job.export_to_dict()


def main():
    if len(sys.argv) != 2:
        print("Usage: %s <shard>" % sys.argv[0])
        sys.exit(1)

    shard = int(sys.argv[1])
    w = Worker(
        all_operation_queues, name=f"Worker:{shard}", connection=redis_connection
    )
    w.work()


if __name__ == "__main__":
    main()

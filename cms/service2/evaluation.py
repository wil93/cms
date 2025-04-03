#!/usr/bin/env python3

"""Evaluation service. It takes care of receiving submissions from the
contestants, transforming them in operations (compilation, execution,
...), queuing them with the right priority, and dispatching them to
the workers. Also, it collects the results from the workers and build
the current ranking.

"""

import logging
from rq import Queue, Worker
from rq.job import Job
from sqlalchemy.orm import Session

from cms.db import (
    SessionGen,
    Digest,
    Dataset,
    Evaluation,
    Submission,
    SubmissionResult,
    Testcase,
    UserTest,
    UserTestResult,
    get_submissions,
    get_submission_results,
    get_datasets_to_judge,
)
from cms.grading.Job import JobGroup, BaseJob, CompilationJob, EvaluationJob
from cms.service2.operations import (
    ESOperation,
    # submission_should_compile,
    submission_to_compile_operation,
    # submission_should_evaluate,
    submission_to_evaluate_operations,
    get_relevant_operations,
    get_submissions_operations,
    get_user_tests_operations,
    user_test_get_operations,
)

from . import redis_connection
from .queues import (
    choose_queue_for_operation_and_priority,
    new_submission_queue,
    scoring_queue,
)
from .worker import process_compilation_job, process_evaluation_job
from .scoring import process_scoring_job

logger = logging.getLogger(__name__)


def process_new_submission(submission_id: int):
    """This function is invoked when a new submission is received. ES takes the
    right countermeasures, i.e., it schedules the necessary jobs (compilation,
    evaluation, scoring).

    submission_id (int): the id of the new submission.

    """
    logger.info("Processing New submission %d.", submission_id)
    with SessionGen() as session:
        submission = Submission.get_from_id(submission_id, session)
        if submission is None:
            logger.error(
                "[new_submission] Couldn't find submission %d in the database.",
                submission_id,
            )
            return

        _enqueue_operations_for_submission(submission, session)


def _enqueue_operations_for_submission(submission: Submission, session: Session):
    """Push in queue the operations required by a submission.

    submission (Submission): a submission.

    return (int): the number of actually enqueued operations.

    """
    for dataset in get_datasets_to_judge(submission.task):
        submission_result = submission.get_result_or_create(dataset)
        session.commit()

        # Create compile job
        compile_job = None
        # if submission_should_compile(submission_result):
        operation, priority, timestamp = submission_to_compile_operation(
            submission_result, submission, dataset
        )
        compile_job = _enqueue(operation, priority, timestamp, session)

        # Create evaluation jobs
        evaluate_jobs = []
        # if submission_should_evaluate(submission_result):
        for operation, priority, timestamp in submission_to_evaluate_operations(
            submission_result, submission, dataset
        ):
            evaluate_jobs.append(
                _enqueue(
                    operation, priority, timestamp, session, depends_on=compile_job
                )
            )

        # Create scoring job
        scoring_queue.enqueue(
            process_scoring_job,
            submission.id,
            dataset.id,
            depends_on=evaluate_jobs,
        )


def _mark_compilation_success(job: Job, connection, _compilation_job: dict):
    """Callback to mark compilation as successful."""
    # TODO: also support USER_TEST_COMPILATION
    # TODO: here we must make a copy of _compilation_job, because otherwise it
    #       gets modified and later the evaluations will receive the wrong
    #       compilation job as "parent" job.
    compilation_job = BaseJob.import_from_dict_with_type(_compilation_job.copy())

    submission_id = compilation_job.operation.object_id
    dataset_id = compilation_job.operation.dataset_id

    with SessionGen() as session:
        submission = Submission.get_from_id(submission_id, session)
        dataset = Dataset.get_from_id(dataset_id, session)

        submission_result = submission.get_result(dataset)
        if submission_result is None:
            # It means it was not even compiled (for some reason).
            raise ValueError(
                "Submission result %d(%d) was not found." % (submission_id, dataset_id)
            )

        compilation_job.to_submission(submission_result)

        session.commit()
        logger.info(
            "Compilation for submission %d marked as successful.", submission_id
        )


def _enqueue(
    operation: ESOperation,
    priority: int,
    timestamp: float,
    session: Session,
    depends_on=None,
) -> Job:
    q = choose_queue_for_operation_and_priority(operation, priority)

    if operation.for_submission():
        submission_or_usertest = Submission.get_from_id(operation.object_id, session)
    else:
        submission_or_usertest = UserTest.get_from_id(operation.object_id, session)
    dataset = Dataset.get_from_id(operation.dataset_id, session)

    cms_job = BaseJob.from_operation(operation, submission_or_usertest, dataset)

    if isinstance(cms_job, CompilationJob):
        return q.enqueue(
            process_compilation_job,
            cms_job.export_to_dict(),
            depends_on=depends_on,
            on_success=_mark_compilation_success,
        )
    elif isinstance(cms_job, EvaluationJob):
        return q.enqueue(
            process_evaluation_job, cms_job.export_to_dict(), depends_on=depends_on
        )
    else:
        raise ValueError(
            "Unknown job type %s for operation %s." % (cms_job.__class__, operation)
        )


def main():
    w = Worker(
        new_submission_queue, name="EvaluationService", connection=redis_connection
    )
    w.work()


if __name__ == "__main__":
    main()

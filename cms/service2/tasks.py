import logging
import os
from typing import List

from celery import Celery, group
from celery.canvas import Signature
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
from cms.db.filecacher import FileCacher
from cms.grading.tasktypes import get_task_type
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
from cms.db.filecacher import TombstoneError

logger = logging.getLogger(__name__)

app = Celery('tasks', backend=os.getenv("REDIS_URL"), broker=os.getenv("RABBITMQ_URL"))

file_cacher = FileCacher()

@app.task
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

        # Create compile job signature
        compile_signature = None
        # if submission_should_compile(submission_result):
        operation, priority, timestamp = submission_to_compile_operation(
            submission_result, submission, dataset
        )
        compile_signature = _enqueue(operation, priority, timestamp, session)

        # Create evaluation job signatures
        evaluate_signatures = []
        # if submission_should_evaluate(submission_result):
        for operation, priority, timestamp in submission_to_evaluate_operations(
            submission_result, submission, dataset
        ):
            evaluate_signatures.append(
                _enqueue(operation, priority, timestamp, session)
            )

        (
            compile_signature
            | mark_compilation_success.s()
            | group(evaluate_signatures)
            | process_scoring_job.s(submission.id, dataset.id)
        )()


@app.task
def mark_compilation_success(_compilation_job: dict):
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

    return _compilation_job


def _enqueue(
    operation: ESOperation,
    priority: int,
    timestamp: float,
    session: Session,
    depends_on=None,
) -> Signature:
    # q = choose_queue_for_operation_and_priority(operation, priority)

    if operation.for_submission():
        submission_or_usertest = Submission.get_from_id(operation.object_id, session)
    else:
        submission_or_usertest = UserTest.get_from_id(operation.object_id, session)
    dataset = Dataset.get_from_id(operation.dataset_id, session)

    cms_job = BaseJob.from_operation(operation, submission_or_usertest, dataset)

    if isinstance(cms_job, CompilationJob):
        return process_compilation_job.s(cms_job.export_to_dict())
    elif isinstance(cms_job, EvaluationJob):
        return process_evaluation_job.s(cms_job.export_to_dict())
    else:
        raise ValueError(
            "Unknown job type %s for operation %s." % (cms_job.__class__, operation)
        )



@app.task
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


@app.task
def process_evaluation_job(_compilation_job: dict, _evaluation_job: dict) -> dict:
    """This function is called by the worker to process an evaluation job.

    evaluation_job (EvaluationJob): the evaluation job to process.

    """
    evaluation_job = BaseJob.import_from_dict_with_type(_evaluation_job)

    logger.info("Starting evaluation job.", extra={"operation": evaluation_job.info})

    if _compilation_job is None:
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
        cms_job = BaseJob.import_from_dict_with_type(_compilation_job)
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


@app.task
def process_scoring_job(evaluation_results: List, submission_id: int, dataset_id: int):
    """Assign a score to a submission result.

    This is the core of ScoringService: here we retrieve the result
    from the database, check if it is in the correct status,
    instantiate its ScoreType, compute its score, store it back in
    the database and tell ProxyService to update RWS if needed.

    submission_id (int): the id of the submission.
    dataset_id (int): the id of the dataset.

    """
    with SessionGen() as session:
        submission = Submission.get_from_id(submission_id, session)
        if submission is None:
            raise ValueError("Submission %d not found in the database." % submission_id)

        dataset = Dataset.get_from_id(dataset_id, session)
        if dataset is None:
            raise ValueError("Dataset %d not found in the database." % dataset_id)

        submission_result = submission.get_result(dataset)

        if submission_result is None:
            # It means it was not even compiled (for some reason).
            raise ValueError(
                "Submission result %d(%d) was not found." % (submission_id, dataset_id)
            )

        expected_evaluation_results = len(dataset.testcases)
        if len(evaluation_results) != expected_evaluation_results:
            # This can happen when:
            #  1) This is a re-scoring which should re-use the old evaluation data.
            #  2) The evaluation took so long (e.g. there were many testcases with
            #     high time limit, or too few workers) that some of the evaluation
            #     results have expired their TTL.
            logger.warning(
                f"There are {len(evaluation_results)} parent evaluation jobs "
                f"available in the queue, but the dataset has {expected_evaluation_results} "
                "testcases. This could be due to a re-scoring or expired "
                "evaluation jobs."
            )

        for result in evaluation_results:
            # if job.get_status() != JobStatus.FINISHED:
            #     logger.warning(
            #         f"Job {job.id} for {submission_id} has status '{job.get_status()}'"
            #         ", this is not expected."
            #     )

            # if job.result is None:
            #     logger.warning(
            #         f"Job {job.id} for {submission_id} has no result, this is not expected."
            #     )

            cms_job = BaseJob.import_from_dict_with_type(result)
            assert isinstance(cms_job, EvaluationJob)
            cms_job.to_submission(submission_result)

        # Set the evaluation outcome.
        submission_result.set_evaluation_outcome()

        # Commit the updated submission result, with the new evaluations.
        session.commit()

        # Check if it's ready to be scored.
        if not submission_result.needs_scoring():
            if submission_result.scored():
                logger.info(
                    "Submission result %d(%d) is already scored.",
                    submission_id,
                    dataset_id,
                )
                return
            else:
                raise ValueError(
                    "The state of the submission result %d(%d) doesn't allow scoring."
                    % (submission_id, dataset_id)
                )

        # Instantiate the score type.
        score_type = dataset.score_type_object

        # Compute score and fill it in the database.
        (
            submission_result.score,
            submission_result.score_details,
            submission_result.public_score,
            submission_result.public_score_details,
            submission_result.ranking_score_details,
        ) = score_type.compute_score(submission_result)

        # Commit the changes.
        session.commit()

        # If dataset is the active one, update RWS.
        # if dataset is submission.task.active_dataset:
        #     logger.info(
        #         "Submission scored %.1f seconds after submission",
        #         (make_datetime() - submission.timestamp).total_seconds(),
        #     )
        #     self.proxy_service.submission_scored(submission_id=submission.id)

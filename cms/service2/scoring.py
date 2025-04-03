import logging
from typing import List

from rq import Worker, get_current_job
from rq.job import Job, JobStatus

from cms.db import Submission, Dataset
from cms.db.session import SessionGen
from cms.grading.Job import BaseJob, EvaluationJob

from . import redis_connection
from .queues import scoring_queue

logger = logging.getLogger(__name__)


def _get_evaluation_jobs() -> List[Job]:
    """Get the evaluation jobs (i.e. the dependencies) of the current job.

    return ([Job]): the list of evaluation jobs that we depend on.

    """
    job = get_current_job()
    if job is None:
        # This can never happen (as long as the function was triggered via RQ)
        return []

    return job.fetch_dependencies()


def process_scoring_job(submission_id: int, dataset_id: int):
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

        expected_evaluation_jobs = len(dataset.testcases)
        evaluation_jobs = _get_evaluation_jobs()
        if len(evaluation_jobs) != expected_evaluation_jobs:
            # This can happen when:
            #  1) This is a re-scoring which should re-use the old evaluation data.
            #  2) The evaluation took so long (e.g. there were many testcases with
            #     high time limit, or too few workers) that some of the evaluation
            #     results have expired their TTL.
            logger.warning(
                f"There are {len(evaluation_jobs)} parent evaluation jobs "
                f"available in the queue, but the dataset has {expected_evaluation_jobs} "
                "testcases. This could be due to a re-scoring or expired "
                "evaluation jobs."
            )

        for job in evaluation_jobs:
            if job.get_status() != JobStatus.FINISHED:
                logger.warning(
                    f"Job {job.id} for {submission_id} has status '{job.get_status()}'"
                    ", this is not expected."
                )

            if job.result is None:
                logger.warning(
                    f"Job {job.id} for {submission_id} has no result, this is not expected."
                )

            cms_job = BaseJob.import_from_dict_with_type(job.result)
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

        return submission_result


def main():
    w = Worker(scoring_queue, name="ScoringService", connection=redis_connection)
    w.work()


if __name__ == "__main__":
    main()

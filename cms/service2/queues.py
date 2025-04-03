import typing

from rq import Queue

# We just need the enum values (COMPILATION, EVALUATION, ...)
from cms.service2.operations import ESOperation

# We just need the priority values (HIGH, MEDIUM, LOW, ...)
from cms.io.priorityqueue import PriorityQueue

from . import redis_connection

# To enqueue new submissions (e.g. from ContestWebServer)
new_submission_queue = Queue("new_submission", connection=redis_connection)

# To enqueue scoring jobs, each of which depends on a set of evaluation jobs
scoring_queue = Queue("scoring", connection=redis_connection)

# To store all the evaluation jobs (compilation, evaluation, user test
# compilation, user test evaluation)
all_operation_queues: typing.List[Queue] = []
_operation_queue_map: typing.Dict[tuple[str, int], Queue] = {}

for priority in (
    PriorityQueue.PRIORITY_EXTRA_HIGH,
    PriorityQueue.PRIORITY_HIGH,
    PriorityQueue.PRIORITY_MEDIUM,
    PriorityQueue.PRIORITY_LOW,
):
    for operation in (
        ESOperation.COMPILATION,
        ESOperation.EVALUATION,
        ESOperation.USER_TEST_COMPILATION,
        ESOperation.USER_TEST_EVALUATION,
    ):
        q = Queue(f"{operation}_{priority}", connection=redis_connection)

        all_operation_queues.append(q)
        _operation_queue_map[(operation, priority)] = q

def choose_queue_for_operation_and_priority(
    operation: ESOperation, priority: int
) -> Queue:
    """Return the name of the queue where the operation should be enqueued. For
    example, if the operation is a compilation, and the priority is 3, the queue
    name will be "compile_3".

    operation (ESOperation): the operation to enqueue.
    priority (int): the priority of the operation.

    return (Queue): the selected queue."""
    return _operation_queue_map[(operation.type_, priority)]

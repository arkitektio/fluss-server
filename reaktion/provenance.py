"""The task a run is created through: what a workflow's runs are found by.

A run names its task twice: ``task_id``, the id the client sends, and ``created_through``, the
koherent Task of the request's verified provenance token. The second is what ``shareWorkflow`` and
the ``createdUnder`` filters read; the first is the client's word for it, and must not contradict it.
"""

from koherent.models import Task
from koherent.utils import get_or_create_task
from koherent.vars import get_current_provenance


class TaskMismatchError(ValueError):
    """A run was asked for under one task while the request ran under another."""


def creating_task(task_id: str | None) -> Task | None:
    """The Task the request runs under, to stamp a new run's ``created_through`` with; None without a token.

    A ``task_id`` other than the token's task (``tsk``) is refused before anything is written: a
    run is the run of the task that creates it.
    """
    provenance = get_current_provenance()
    if provenance is None:
        return None
    if task_id is not None and str(task_id) != provenance.tsk:
        raise TaskMismatchError(
            f"This request runs under task {provenance.tsk}; it cannot create the run of task {task_id}"
        )
    return get_or_create_task()

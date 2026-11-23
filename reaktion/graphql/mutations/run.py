import logging

import strawberry
from kante.types import Info

from reaktion import enums, inputs, models, types
from reaktion.provenance import creating_task
from reaktion.scoping import get_for_org

logger = logging.getLogger(__name__)


def create_run(info: Info, input: inputs.CreateRunInput) -> types.Run:
    # Scope through the flow: only flows in the request's organization can be run
    # (raises DoesNotExist for a cross-org / unknown flow).
    flow = get_for_org(models.Flow, info, id=input.flow)
    given = input.to_pydantic()
    task_id = given.task_id
    running = dict(
        snapshot_interval=given.snapshot_interval,
        status=enums.RunStatus.RUNNING.value,
    )
    # Under a provenance token the run is its task's; a resumed task finds the run its first
    # attempt created, and keeps the task that created it.
    task = creating_task(task_id)
    run, created = models.Run.objects.update_or_create(
        flow=flow,
        task_id=task_id,
        defaults=running,
        create_defaults={**running, "created_through": task},
    )

    return run


def close_run(info: Info, input: inputs.CloseRunInput) -> types.Run:
    run = models.Run.objects.get(
        id=input.run, flow__organization=info.context.request.organization
    )
    run.status = enums.RunStatus.COMPLETED.value
    run.save()

    return run


def delete_run(info: Info, input: inputs.DeleteRunInput) -> strawberry.ID:
    run = models.Run.objects.get(
        id=input.run, flow__organization=info.context.request.organization
    )
    run.delete()
    return input.run


def snapshot(info: Info, input: inputs.SnapshotRunInput) -> types.Snapshot:
    # Validate the run belongs to the request's organization before snapshotting.
    run = models.Run.objects.get(
        id=input.run, flow__organization=info.context.request.organization
    )
    snapshot = models.Snapshot.objects.create(run=run, t=input.t)
    return snapshot


def delete_snapshot(info: Info, input: inputs.DeleteSnapshotInput) -> strawberry.ID:
    snapshot = models.Snapshot.objects.get(
        id=input.snapshot, run__flow__organization=info.context.request.organization
    )
    snapshot.delete()
    return input.snapshot


def track(info: Info, input: inputs.TrackInput) -> types.RunEvent:
    # Validate the run belongs to the request's organization before tracking.
    run = models.Run.objects.get(
        id=input.run, flow__organization=info.context.request.organization
    )
    event = models.RunEvent.objects.create(
        reference=input.reference,
        run=run,
        t=input.t,
        kind=input.kind,
        value=input.value,
        caused_by=input.caused_by,
        source=input.source,
        handle=input.handle,
        exception=input.exception,
    )
    return event

import logging

import strawberry
from kante.types import Info

from reaktion import enums, inputs, models, types
from reaktion.scoping import get_for_org

logger = logging.getLogger(__name__)


def create_run(info: Info, input: inputs.CreateRunInput) -> types.Run:
    # Scope through the flow: only flows in the request's organization can be run
    # (raises DoesNotExist for a cross-org / unknown flow).
    flow = get_for_org(models.Flow, info, id=input.flow)
    run, created = models.Run.objects.update_or_create(
        flow=flow,
        task_id=input.task_id,
        defaults=dict(
            snapshot_interval=input.snapshot_interval,
            status=enums.RunStatus.RUNNING.value,
        ),
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

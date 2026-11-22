"""Runs and Python runs as they start, change status and go: for a list, or for one run.

The publisher (``reaktion/signals.py``) sends only ids, to the organization's room and the
run's own; the subscriber re-reads the row through the request's scope, so a guest is told
only of what their collaborations hold. A run deleted between broadcast and re-read is
skipped, not an error.
"""

from collections.abc import AsyncGenerator

import strawberry
from arkitekt_service.collaborations.guests import object_scope
from kante.channel import CRUDSignal
from kante.types import Info

from reaktion import channels, models, types
from reaktion.scoping import aget_for_org


@strawberry.type(
    description="A run started (`create`), changed status (`update`) or was deleted (`delete`, the id only). Exactly one field is set."
)
class RunChange:
    create: types.Run | None = strawberry.field(
        default=None, description="The run that just started."
    )
    update: types.Run | None = strawberry.field(
        default=None, description="The run that just changed, e.g. was completed."
    )
    delete: strawberry.ID | None = strawberry.field(
        default=None, description="The id of the run that was deleted."
    )


@strawberry.type(
    description="A Python run started (`create`), changed status (`update`: reopened, completed, failed, cancelled) or was deleted (`delete`, the id only). Exactly one field is set."
)
class PythonRunChange:
    create: types.PythonRun | None = strawberry.field(
        default=None, description="The run that just started."
    )
    update: types.PythonRun | None = strawberry.field(
        default=None, description="The run that just changed status."
    )
    delete: strawberry.ID | None = strawberry.field(
        default=None, description="The id of the run that was deleted."
    )


def _scoped_runs(info: Info):
    organization = info.context.request.organization
    return object_scope(
        models.Run.objects.filter(flow__organization=organization), info=info
    )


async def _run_change(info: Info, message: CRUDSignal) -> RunChange | None:
    if message.delete is not None:
        return RunChange(delete=strawberry.ID(str(message.delete)))
    run_id = message.create if message.create is not None else message.update
    if run_id is None:
        return None
    run = await _scoped_runs(info).filter(id=run_id).afirst()
    if run is None:
        return None
    return (
        RunChange(create=run) if message.create is not None else RunChange(update=run)
    )


async def runs(info: Info) -> AsyncGenerator[RunChange, None]:
    """Every run of the request's organization as it starts, changes status or is deleted."""
    organization = info.context.request.organization
    async for message in channels.run_channel.listen(
        info, [channels.run_org_group(organization.id)]
    ):
        change = await _run_change(info, message)
        if change is not None:
            yield change


async def run(info: Info, id: strawberry.ID) -> AsyncGenerator[RunChange, None]:
    """One run as it changes status or is deleted; refused for a run outside the organization."""
    found = await _scoped_runs(info).aget(id=id)
    async for message in channels.run_channel.listen(
        info, [channels.run_group(found.id)]
    ):
        change = await _run_change(info, message)
        if change is not None:
            yield change


async def _python_run_change(info: Info, message: CRUDSignal) -> PythonRunChange | None:
    if message.delete is not None:
        return PythonRunChange(delete=strawberry.ID(str(message.delete)))
    run_id = message.create if message.create is not None else message.update
    if run_id is None:
        return None
    try:
        found = await aget_for_org(models.PythonRun, info, id=run_id)
    except models.PythonRun.DoesNotExist:
        return None
    return (
        PythonRunChange(create=found)
        if message.create is not None
        else PythonRunChange(update=found)
    )


async def python_runs(info: Info) -> AsyncGenerator[PythonRunChange, None]:
    """Every Python run of the request's organization as it starts, changes status or is deleted."""
    organization = info.context.request.organization
    async for message in channels.python_run_channel.listen(
        info, [channels.python_run_org_group(organization.id)]
    ):
        change = await _python_run_change(info, message)
        if change is not None:
            yield change


async def python_run(
    info: Info, id: strawberry.ID
) -> AsyncGenerator[PythonRunChange, None]:
    """One Python run as it changes status or is deleted; refused for a run outside the organization."""
    found = await aget_for_org(models.PythonRun, info, id=id)
    async for message in channels.python_run_channel.listen(
        info, [channels.python_run_group(found.id)]
    ):
        change = await _python_run_change(info, message)
        if change is not None:
            yield change

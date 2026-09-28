"""PythonFlow versions and their runs.

A version's behaviour (source, entrypoint, manifest, runtime) is immutable: posting new content
makes a new version in the same lineage, posting the same content returns the existing one. Its
lifecycle is DRAFT → PUBLISHED ⇄ ARCHIVED: an archived version can be published again (reverting
to earlier content lands on that very version), a draft may be deleted, a published version is
archived instead (its runs keep pointing at it).
"""

import logging
import uuid

import strawberry
from django.db import transaction
from django.utils import timezone
from kante.types import Info

from reaktion import enums, inputs, models, types
from reaktion.hashers import hash_python_flow
from reaktion.scoping import for_org, get_for_org

logger = logging.getLogger(__name__)

Status = enums.PythonFlowStatusChoices


def create_python_flow(info: Info, input: inputs.CreatePythonFlowInput) -> types.PythonFlow:
    request = info.context.request
    # Validate the ports and manifest through their pydantic models and store the normalised dump.
    model = input.to_pydantic()
    manifest = [entry.model_dump(mode="json") for entry in model.manifest]

    previous = get_for_org(models.PythonFlow, info, id=model.previous) if model.previous else None
    lineage = previous.lineage if previous else uuid.uuid4()

    flow, created = models.PythonFlow.objects.get_or_create(
        organization=request.organization,
        lineage=lineage,
        hash=hash_python_flow(model.source, model.entrypoint, manifest, model.runtime),
        defaults=dict(
            previous=previous,
            title=model.title or (previous.title if previous else "Untitled Python Flow"),
            description=model.description if model.description is not None else (previous.description if previous else None),
            creator=request.user,
            source=model.source,
            entrypoint=model.entrypoint,
            args=[port.model_dump(mode="json") for port in model.args],
            returns=[port.model_dump(mode="json") for port in model.returns],
            manifest=manifest,
            runtime=model.runtime,
        ),
    )
    if not created:
        logger.debug("PythonFlow %s already holds this content; returning it", flow.id)
    return flow


def update_python_flow(info: Info, input: inputs.UpdatePythonFlowInput) -> types.PythonFlow:
    flow = get_for_org(models.PythonFlow, info, id=input.id)
    if input.title is not None:
        flow.title = input.title
    if input.description is not None:
        flow.description = input.description
    flow.save()
    return flow


def _transition(info: Info, id: strawberry.ID, sources: tuple[Status, ...], target: Status) -> models.PythonFlow:
    """Move one version from one of ``sources`` to ``target``; the row lock serialises concurrent calls."""
    with transaction.atomic():
        flow = for_org(models.PythonFlow, info).select_for_update().get(id=id)
        if flow.status not in sources:
            raise ValueError(f"Only a {' or '.join(s.value for s in sources)} PythonFlow can become {target.value}; this one is {flow.status}")
        flow.status = target.value
        flow.save()
    return flow


def publish_python_flow(info: Info, input: inputs.PythonFlowRefInput) -> types.PythonFlow:
    return _transition(info, input.id, (Status.DRAFT, Status.ARCHIVED), Status.PUBLISHED)


def archive_python_flow(info: Info, input: inputs.PythonFlowRefInput) -> types.PythonFlow:
    return _transition(info, input.id, (Status.PUBLISHED,), Status.ARCHIVED)


def delete_python_flow(info: Info, input: inputs.PythonFlowRefInput) -> strawberry.ID:
    with transaction.atomic():
        flow = for_org(models.PythonFlow, info).select_for_update().get(id=input.id)
        if flow.status != Status.DRAFT:
            raise ValueError(f"Only a DRAFT PythonFlow can be deleted; archive this {flow.status} one instead")
        flow.delete()
    return input.id


def create_python_run(info: Info, input: inputs.CreatePythonRunInput) -> types.PythonRun:
    flow = get_for_org(models.PythonFlow, info, id=input.flow)
    if flow.status != Status.PUBLISHED:
        raise ValueError(f"Only a PUBLISHED PythonFlow can be run; this one is {flow.status}")
    run, _ = models.PythonRun.objects.get_or_create(flow=flow, task_id=input.task_id)
    return run


def close_python_run(info: Info, input: inputs.ClosePythonRunInput) -> types.PythonRun:
    run = get_for_org(models.PythonRun, info, id=input.run)
    if input.status == enums.PythonRunStatus.RUNNING:
        raise ValueError("A run is closed as COMPLETED or FAILED, not RUNNING")
    run.status = input.status.value
    run.finished_at = timezone.now()
    run.save()
    return run

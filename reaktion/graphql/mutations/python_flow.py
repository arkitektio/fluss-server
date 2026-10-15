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

from reaktion import enums, inputs, models, python_flows, types
from reaktion.hashers import hash_python_flow
from reaktion.scoping import for_org, get_for_org

logger = logging.getLogger(__name__)

Status = enums.PythonFlowStatusChoices
RunStatus = enums.PythonRunStatusChoices


def create_python_flow(info: Info, input: inputs.CreatePythonFlowInput) -> types.PythonFlow:
    """Validate the source and store what the validation derived; a source that does not validate is refused."""
    request = info.context.request
    model = input.to_pydantic()
    report = python_flows.validate(model)
    if not report.ok:
        raise ValueError(python_flows.refusal(report))
    manifest = python_flows.manifest(report)

    previous = get_for_org(models.PythonFlow, info, id=model.previous) if model.previous else None
    lineage = previous.lineage if previous else uuid.uuid4()

    # Ports are derived from source, entrypoint and the manifest's actions, so the hash need not
    # cover them: identical content derives identical ports.
    flow, created = models.PythonFlow.objects.get_or_create(
        organization=request.organization,
        lineage=lineage,
        hash=hash_python_flow(model.source, model.entrypoint, manifest, report.runtime),
        defaults=dict(
            previous=previous,
            title=model.title or (previous.title if previous else "Untitled Python Flow"),
            description=model.description if model.description is not None else (previous.description if previous else None),
            creator=request.user,
            source=model.source,
            entrypoint=model.entrypoint,
            args=python_flows.arg_ports(report.args),
            returns=python_flows.return_ports(report.returns),
            manifest=manifest,
            runtime=report.runtime,
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
    """The run of a task: a task resumed after its agent died gets its run again, running.

    It runs again from the start, so a run the first attempt closed before it died is
    reopened; it keeps its ``created_at``, which is the clock the flow sees.
    """
    flow = get_for_org(models.PythonFlow, info, id=input.flow)
    if flow.status != Status.PUBLISHED:
        raise ValueError(f"Only a PUBLISHED PythonFlow can be run; this one is {flow.status}")
    with transaction.atomic():
        run, created = models.PythonRun.objects.select_for_update().get_or_create(flow=flow, task_id=input.task_id)
        if not created and run.status != RunStatus.RUNNING:
            run.status = RunStatus.RUNNING.value
            run.finished_at = None
            run.save()
    return run


def close_python_run(info: Info, input: inputs.ClosePythonRunInput) -> types.PythonRun:
    """End a RUNNING run; the row lock makes two closes of one run one close and one refusal."""
    if input.status == enums.PythonRunStatus.RUNNING:
        raise ValueError("A run is closed as COMPLETED, FAILED or CANCELLED, not RUNNING")
    with transaction.atomic():
        run = for_org(models.PythonRun, info).select_for_update().get(id=input.run)
        if run.status != RunStatus.RUNNING:
            raise ValueError(f"Only a RUNNING PythonRun can be closed; this one is {run.status}")
        run.status = input.status.value
        run.finished_at = timezone.now()
        run.save()
    return run

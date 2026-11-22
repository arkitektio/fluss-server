import logging

import strawberry
from kante.types import Info

from reaktion import models, types

logger = logging.getLogger(__name__)


@strawberry.input
class CreateTraceInput:
    flow: strawberry.ID
    provision: strawberry.ID
    snapshot_interval: int | None = None


def create_trace(info: Info, input: CreateTraceInput) -> types.Trace:
    trace, created = models.Trace.objects.update_or_create(
        flow_id=input.flow,
        provision_id=input.provision,
        defaults=dict(snapshot_interval=input.snapshot_interval),
    )

    return trace

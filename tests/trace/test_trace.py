"""Trace model-level tests.

Trace has no GraphQL surface in fluss (create_trace is not wired into the
schema Mutation, and there is no trace query), so it is exercised at the ORM
level via the factory to keep the domain covered.
"""

import pytest

from reaktion.models import Trace, TraceEvent, TraceSnapshot
from tests.utils import MakeTrace

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_make_trace(make_trace: MakeTrace) -> None:
    trace = await make_trace(provision={"foo": "bar"})
    assert await Trace.objects.filter(id=trace.pk).aexists()
    assert trace.flow_id is not None
    assert trace.provision == {"foo": "bar"}


async def test_trace_snapshot_and_event(make_trace: MakeTrace) -> None:
    trace = await make_trace()
    snap = await TraceSnapshot.objects.acreate(trace=trace, status="RUNNING")
    event = await TraceEvent.objects.acreate(trace=trace, source="node-1", value="42")
    await event.snapshot.aadd(snap)

    assert await TraceSnapshot.objects.filter(trace_id=trace.pk).aexists()
    assert await TraceEvent.objects.filter(trace_id=trace.pk, source="node-1").aexists()

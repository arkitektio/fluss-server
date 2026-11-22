"""A run's events, heard over a subscriber's websocket: by the run's organization alone."""

import asyncio
from collections.abc import AsyncIterator

import pytest
from asgiref.sync import sync_to_async

from tests.utils import MakeRun

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def _heard(stream: AsyncIterator[dict[str, object]]) -> list[dict]:
    return [message async for message in stream]


async def test_a_run_is_heard_by_its_organization_alone(make_run: MakeRun) -> None:
    from kante.testing import GraphQLWebSocketTestClient

    from fluss_server.asgi import application
    from reaktion.models import RunEvent

    run = await make_run()  # the "test" token's organization
    watch = f'subscription {{ events(run: "{run.pk}") {{ id t }} }}'

    async with (
        GraphQLWebSocketTestClient(
            application, connection_params={"token": "test"}
        ) as member,
        GraphQLWebSocketTestClient(
            application, connection_params={"token": "othertest"}
        ) as stranger,
    ):
        heard = asyncio.ensure_future(
            anext(member.subscribe(watch, timeout=3, max_messages=1))
        )
        overheard = asyncio.ensure_future(_heard(stranger.subscribe(watch, timeout=2)))
        # Let both subscriptions join (or be refused) before the event is tracked.
        await asyncio.sleep(0.3)

        event = await sync_to_async(RunEvent.objects.create)(
            run=run, t=1, source="node"
        )

        message = await heard
        assert message["payload"]["data"]["events"] == {"id": str(event.pk), "t": 1}
        # Another organization's member is not told of the run, nor of anything tracked in it.
        assert not any(
            (message["payload"].get("data") or {}).get("events")
            for message in await overheard
        )

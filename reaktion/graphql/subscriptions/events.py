from kante.types import Info
import strawberry
from reaktion import types, models, scalars, channel_signals, channels
from typing import AsyncGenerator


async def events(
    self,
    info: Info,
    run: strawberry.ID,
) -> AsyncGenerator[types.RunEvent, None]:
    """The events tracked in a run of the request's organization, as they are tracked."""

    # Held to the organization like every run read (a run reaches it through its flow): another
    # organization's member is not told the run exists, nor joined to its group.
    run = await models.Run.objects.aget(id=run, flow__organization=info.context.request.organization)

    async for message in channels.run_event_channel.listen(info.context, [f"run_{run.id}"]):
        yield await models.RunEvent.objects.aget(id=message.event)

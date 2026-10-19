import strawberry
from kante.types import Info
from reaktion import models, types
from arkitekt_service.collaborations.guests import object_scope


def events_between(
    info: Info, run: strawberry.ID, min: int | None = None, max: int | None = None
) -> list[types.RunEvent]:
    # Scope the run to the request's organization so events of another org's
    # run cannot be read (raises DoesNotExist for a cross-org / unknown run), and,
    # for a guest of the organization, to their collaborations.
    object_scope(models.Run.objects.filter(flow__organization=info.context.request.organization), info=info).get(id=run)

    if min is None:
        min = 0

    snapshot = (
        models.Snapshot.objects.filter(run_id=run, t__lte=min).order_by("-t").first()
    )

    if snapshot:
        min = snapshot.t
        start_events = list(snapshot.events.all())
    else:
        start_events = []

    events = models.RunEvent.objects.filter(run_id=run, t__gte=min)

    if max:
        events = events.filter(t__lte=max)

    events = events.order_by("t").all()

    return start_events + list(events)

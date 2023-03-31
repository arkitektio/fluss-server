from email.policy import default
from balder.types import BalderMutation
import graphene
from flow import models, types
from lok import bounced
import logging
from graphene.types.generic import GenericScalar
from flow.enums import EventTypeInput
from flow.scalars import EventValue
from flow.inputs import RunEventInput

logger = logging.getLogger(__name__)


class Start(BalderMutation):
    class Arguments:
        assignation = graphene.ID(required=True)
        flow = graphene.ID(required=True)

    @bounced(anonymous=False)
    def mutate(root, info, assignation, flow):
        run, created = models.Run.objects.get_or_create(
            flow_id=flow, assignation=assignation
        )
        return run

    class Meta:
        type = types.Run
        operation = "start"


class DeleteRunReturn(graphene.ObjectType):
    id = graphene.ID(required=True)


class DeleteRun(BalderMutation):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def mutate(root, info, id=None):
        graph = models.Run.objects.get(id=id)
        graph.delete()
        return {"id": id}

    class Meta:
        type = DeleteRunReturn


class Log(BalderMutation):
    class Arguments:
        run = graphene.ID(required=True)
        message = graphene.String(required=True)

    @bounced(anonymous=False)
    def mutate(root, info, run, message):
        log = models.RunLog.objects.create(run_id=run, log=message)
        return log

    class Meta:
        type = types.RunLog
        operation = "alog"


class Snapshot(BalderMutation):
    class Arguments:
        run = graphene.ID(required=True)
        events = graphene.List(
            graphene.ID,
            description="The IDs of the events that make up the snapshot",
            required=True,
        )
        t = graphene.Int(required=True)

    @bounced(anonymous=False)
    def mutate(root, info, run, events, t):
        s = models.Snapshot.objects.create(run_id=run, t=t)
        s.events.set(events)
        return s

    class Meta:
        type = types.Snapshot
        operation = "snapshot"


class DeleteSnapshotReturn(graphene.ObjectType):
    id = graphene.ID(required=True)


class DeleteSnapshot(BalderMutation):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def mutate(root, info, id=None):
        graph = models.Snapshot.objects.get(id=id)
        graph.delete()
        return {"id": id}

    class Meta:
        type = DeleteSnapshotReturn


class Track(BalderMutation):
    class Arguments:
        source = graphene.String(required=True)
        handle = graphene.String(required=True)
        t = graphene.Int(required=True)
        type = graphene.Argument(EventTypeInput, required=True)
        run = graphene.ID(required=True)
        value = EventValue(required=False)
        caused_by = graphene.List(graphene.Int, required=True)

    @bounced(anonymous=False)
    def mutate(root, info, run, source, handle, type, t, caused_by, value=None):
        log = models.RunEvent.objects.create(
            run_id=run,
            source=source,
            handle=handle,
            type=type,
            value=value,
            t=t,
            caused_by=caused_by,
        )
        return log

    class Meta:
        type = types.RunEvent
        operation = "track"

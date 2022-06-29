from email.policy import default
from balder.types import BalderMutation
import graphene
from flow import models, types
from lok import bounced
import logging
from graphene.types.generic import GenericScalar

logger = logging.getLogger(__name__)


class Start(BalderMutation):
    class Arguments:
        assignation = graphene.ID(required=True)
        flow = graphene.ID(required=True)

    @bounced(anonymous=False)
    def mutate(root, info, assignation, flow):
        run = models.Run.objects.create(flow_id=flow, assignation=assignation)
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
        state = GenericScalar(required=True)

    @bounced(anonymous=False)
    def mutate(root, info, run, state):
        log = models.Snapshot.objects.create(run_id=run, state=state)
        return log

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

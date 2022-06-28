from email.policy import default
from balder.types import BalderMutation
import graphene
from flow import models, types
from lok import bounced
import logging

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

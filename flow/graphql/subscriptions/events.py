from balder.types import BalderSubscription
from lok import bounced
import graphene
from flow import models, types
import logging

logger = logging.getLogger(__name__)


class Event(graphene.ObjectType):
    deleted = graphene.ID()
    update = graphene.Field(types.RunEvent)
    create = graphene.Field(types.RunEvent)


class EventsSubscription(BalderSubscription):
    RUNGROUP = lambda run: f"events_{run.id}"

    class Arguments:
        id = graphene.ID(
            description="The id of the run you want to listen to", required=True
        )

    class Meta:
        type = Event
        operation = "events"

    def publish(payload, info, *args, **kwargs):
        payload = payload["payload"]
        action = payload["action"]
        data = payload["data"]

        logger.error(payload)

        if action == "updated":
            return {"update": data}
        if action == "created":
            return {"create": data}
        if action == "deleted":
            return {"deleted": data}

        logger.error("error in payload")

    @bounced(only_jwt=True)
    def subscribe(root, info, id):
        run = models.Run.objects.get(id=id)
        return [EventsSubscription.RUNGROUP(run)]

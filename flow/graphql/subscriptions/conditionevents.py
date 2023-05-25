from balder.types import BalderSubscription
from lok import bounced
import graphene
from flow import models, types
import logging

logger = logging.getLogger(__name__)


class ConditionEvents(graphene.ObjectType):
    deleted = graphene.ID()
    update = graphene.Field(types.ConditionEvent)
    create = graphene.Field(types.ConditionEvent)


class ConditionEventsSubscription(BalderSubscription):
    CONDITIONGROUP = lambda condition: f"conditionevents_{condition.id}"

    class Arguments:
        id = graphene.ID(
            description="The id of the run you want to listen to", required=True
        )

    class Meta:
        type = ConditionEvents
        operation = "conditionevents"

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
        condition = models.Condition.objects.get(id=id)
        return [ConditionEventsSubscription.CONDITIONGROUP(condition)]

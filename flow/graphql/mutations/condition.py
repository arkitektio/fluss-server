from email.policy import default
from balder.types import BalderMutation
import graphene
from flow import models, types
from lok import bounced
import logging
from graphene.types.generic import GenericScalar
from flow.enums import EventTypeInput, ContractStatus
from flow.scalars import EventValue
from flow.inputs import RunEventInput
from flow.utils import fill_created
logger = logging.getLogger(__name__)


class Start(BalderMutation):
    class Arguments:
        provision = graphene.ID(required=True)
        flow = graphene.ID(required=True)
        snapshot_interval = graphene.Int(required=False)

    @bounced(anonymous=False)
    def mutate(root, info, provision, flow, snapshot_interval=None):
        run, created = models.Condition.objects.get_or_create(
            flow_id=flow, provision=provision, snapshot_interval=snapshot_interval, defaults=fill_created(info)
        )
        return run

    class Meta:
        type = types.Condition
        operation = "create_condition"


class DeleteConditionReturn(graphene.ObjectType):
    id = graphene.ID(required=True)


class DeleteCondition(BalderMutation):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def mutate(root, info, id=None):
        graph = models.Condition.objects.get(id=id)
        graph.delete()
        return {"id": id}

    class Meta:
        type = DeleteConditionReturn


class CreateConditionSnapshot(BalderMutation):
    class Arguments:
        condition = graphene.ID(required=True)
        events = graphene.List(
            graphene.ID,
            description="The IDs of the events that make up the snapshot",
            required=True,
        )

    @bounced(anonymous=False)
    def mutate(root, info, condition, events):
        s = models.ConditionSnapshot.objects.create(condition_id=condition)
        s.events.set(events)
        return s

    class Meta:
        type = types.ConditionSnapshot
        operation = "createConditionSnapshot"


class DeleteConditionSnapshotReturn(graphene.ObjectType):
    id = graphene.ID(required=True)


class DeleteConditionSnapshot(BalderMutation):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def mutate(root, info, id=None):
        graph = models.ConditionSnapshot.objects.get(id=id)
        graph.delete()
        return {"id": id}

    class Meta:
        type = DeleteConditionSnapshotReturn


class Trace(BalderMutation):
    class Arguments:
        source = graphene.String(required=True)
        condition = graphene.ID(required=True)
        state = graphene.Argument(ContractStatus, required=True)
        value = graphene.String(required=False)

    @bounced(anonymous=False)
    def mutate(root, info, condition, source, state, value=None):
        log = models.ConditionEvent.objects.create(
            condition_id=condition,
            source=source,
            value=value,
            state=state,
        )
        return log

    class Meta:
        type = types.ConditionEvent
        operation = "trace"


class PinCondition(BalderMutation):
    """Pin Condition
    
    This mutation pins an Runs and returns the pinned Run."""

    class Arguments:
        id = graphene.ID(required=True, description="The ID of the representation")
        pin = graphene.Boolean(required=True, description="The pin state")

    @bounced()
    def mutate(root, info, id, pin, **kwargs):
        rep = models.Condition.objects.get(id=id)
        if pin:
            rep.pinned_by.add(info.context.user)
        else:
            rep.pinned_by.remove(info.context.user)
        rep.save()
        return rep

    class Meta:
        type = types.Condition
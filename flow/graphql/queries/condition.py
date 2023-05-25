from balder.types.mutation.base import BalderMutation
from balder.types import BalderQuery
import graphene
from flow import models, types, filters
from lok import bounced


class Condition(BalderQuery):
    class Arguments:
        id = graphene.ID(required=False, description="The Id of the Graph")
        provision = graphene.ID(
            required=False, description="The assignation of the Graph"
        )

    def resolve(root, info, provision=None, id=None):
        if provision:
            graph = models.Condition.objects.get(provision=provision)
        elif id:
            graph = models.Condition.objects.get(id=id)
        else:
            raise Exception("No id or assignation provided")
        return graph

    class Meta:
        type = types.Condition


class ConditionEventsBetween(BalderQuery):
    class Arguments:
        condition = graphene.ID(required=True)
        min = graphene.DateTime(required=False)
        max = graphene.DateTime(required=False)

    def resolve(root, info, condition, min=0, max=None):
        snapshot = (
            models.ConditionSnapshot.objects.filter(condition_id=condition, created_at__lte=min)
            .order_by("-created_at")
            .first()
        )

        if snapshot:
            min = snapshot.created_at
            start_events = list(snapshot.events.all())
        else:
            start_events = []

        events = models.ConditionEvent.objects.filter(condition_id=condition, created_at__gte=min)

        if max:
            events = events.filter(t__lte=max)

        events = events.order_by("created_at").all()

        return start_events + list(events)

    class Meta:
        type = types.ConditionEvent
        list = True
        operation = "conditionEventsBetween"


class ConditionSnapshot(BalderQuery):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def resolve(root, info, id=None):
        graph = models.ConditionSnapshot.objects.get(id=id)
        return graph

    class Meta:
        type = types.ConditionSnapshot


class Conditions(BalderQuery):
    class Meta:
        type = types.Condition
        list = True
        paginate = True
        filter = filters.ConditionFilter


class MyConditions(BalderQuery):
    class Meta:
        type = types.Condition
        list = True
        operation = "myconditions"
        personal = "created_by"
        paginate = True
        filter = filters.ConditionFilter


class ConditionSnapshots(BalderQuery):
    class Meta:
        type = types.ConditionSnapshot
        list = True
        filter = filters.ConditionSnapshotFilter

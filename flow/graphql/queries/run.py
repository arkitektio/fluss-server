from balder.types.mutation.base import BalderMutation
from balder.types import BalderQuery
import graphene
from flow import models, types, filters
from lok import bounced


class Run(BalderQuery):
    class Arguments:
        id = graphene.ID(required=False, description="The Id of the Graph")
        assignation = graphene.ID(
            required=False, description="The assignation of the Graph"
        )

    def resolve(root, info, assignation=None, id=None):
        if assignation:
            graph = models.Run.objects.get(assignation=assignation)
        elif id:
            graph = models.Run.objects.get(id=id)
        else:
            raise Exception("No id or assignation provided")
        return graph

    class Meta:
        type = types.Run


class EventsBetween(BalderQuery):
    class Arguments:
        run = graphene.ID(required=True)
        min = graphene.Int(required=False)
        max = graphene.Int(required=False)

    def resolve(root, info, run, min=0, max=None):
        snapshot = (
            models.Snapshot.objects.filter(run_id=run, t__lte=min)
            .order_by("-t")
            .first()
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

    class Meta:
        type = types.RunEvent
        list = True
        operation = "eventsBetween"


class Snapshot(BalderQuery):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def resolve(root, info, id=None):
        graph = models.Snapshot.objects.get(id=id)
        return graph

    class Meta:
        type = types.Snapshot


class Runs(BalderQuery):
    class Meta:
        type = types.Run
        list = True
        paginate = True
        filter = filters.RunFilter

class MyRuns(BalderQuery):
    class Meta:
        type = types.Run
        list = True
        personal = "created_by"
        operation= "myruns"
        paginate = True
        filter = filters.RunFilter

class RunLogs(BalderQuery):
    class Meta:
        type = types.RunLog
        list = True
        filter = filters.RunLogFilter


class Snapshots(BalderQuery):
    class Meta:
        type = types.Snapshot
        list = True
        filter = filters.SnapshotFilter

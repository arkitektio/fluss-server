from balder.types.mutation.base import BalderMutation
from balder.types import BalderQuery
import graphene
from flow import models, types, filters
from lok import bounced


class Run(BalderQuery):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def resolve(root, info, id=None):
        graph = models.Run.objects.get(id=id)
        return graph

    class Meta:
        type = types.Run


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

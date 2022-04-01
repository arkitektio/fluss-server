from balder.types.mutation.base import BalderMutation
from balder.types import BalderQuery
import graphene
from flow import models, types
from lok import bounced


class Flow(BalderQuery):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def resolve(root, info, id=None):
        graph = models.Flow.objects.get(id=id)
        return graph

    class Meta:
        type = types.Flow


class Flows(BalderQuery):
    class Meta:
        type = types.Flow
        list = True


class FlowDetail(BalderQuery):
    class Arguments:
        id = graphene.ID(description="A unique ID for this Graph")

    @bounced(anonymous=False)
    def resolve(root, info, *args, id=None, template=None, node=None):
        return models.Flow.objects.get(id=id)

    class Meta:
        type = types.Flow
        operation = "flow"


class MyFlows(BalderQuery):
    class Meta:
        list = True
        personal = "creator"
        type = types.Flow
        operation = "myflows"

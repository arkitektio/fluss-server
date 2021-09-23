from balder.types.mutation.base import BalderMutation
from balder.types import BalderQuery
import graphene
from flow import models, types
from lok import bounced

class Graph(BalderQuery):

    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def resolve(root, info, id=None):
        graph = models.Graph.objects.get(id=id)
        return graph

    class Meta:
        type = types.Graph

class Graphs(BalderQuery):

    class Meta:
        type = types.Graph
        list = True


class GraphDetail(BalderQuery):

    class Arguments:
        id = graphene.ID(description="A unique ID for this Graph")
        template = graphene.ID(description="The corresponding template on arkitekt (proxied through FlowTemplate)")
        node = graphene.ID(description="The corresponding node on arkitekt (proxied through FlowNode)")


    @bounced(anonymous=False)
    def resolve(root, info , *args,  id=None, template=None, node=None):
        if template: return models.Graph.objects.get(template__arkitekt_id=template)
        if node: return models.Graph.objects.get(node__arkitekt_id=node)
        if id: return models.Graph.objects.get(id=id)


    class Meta:
        type = types.Graph
        operation = "graph"


class MyGraphs(BalderQuery):


    class Meta:
        list = True
        personal = "creator"
        type = types.Graph
        operation = "mygraphs"

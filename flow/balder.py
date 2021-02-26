from balder.types import BalderQuery
from flow import types
from flow import models
import graphene
from herre import bounced

class GraphDetail(BalderQuery):

    class Arguments:
        id = graphene.ID(description="A unique ID for this Graph")


    @bounced()
    def resolve(root, info , *args,  id=None):
        return models.Graph.objects.get(id=id)


    class Meta:
        type = types.Graph
        operation = "graph"


class MyGraphs(BalderQuery):


    class Meta:
        list = True
        personal = "creator"
        type = types.Graph
        operation = "mygraphs"


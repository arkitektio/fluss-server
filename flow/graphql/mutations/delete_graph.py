from balder.types import BalderMutation
import graphene
from flow import models, types
from herre import bounced

class DeleteGraphOut(graphene.ObjectType):
    id = graphene.ID()

class DeleteGraph(BalderMutation):

    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def mutate(root, info, id=None):

        graph = models.Graph.objects.get(id=id)
        graph.delete()
        return {"id": id}

    class Meta:
        type = DeleteGraphOut

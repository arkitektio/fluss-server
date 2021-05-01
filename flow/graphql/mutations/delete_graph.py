from balder.types import BalderMutation
import graphene
from flow import models, types
from herre import bounced

class DeleteGraphOut(graphene.ObjectType):
    ok = graphene.Boolean()

class DeleteGraph(BalderMutation):

    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def mutate(root, info, id=None):

        graph = models.Graph.objects.get(id=id)
        graph.delete()
        return {"ok": True}

    class Meta:
        type = DeleteGraphOut

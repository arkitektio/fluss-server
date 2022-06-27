from email.policy import default
from balder.types import BalderMutation
import graphene
from flow import models, types
from lok import bounced
import logging
from flow.inputs import GraphInput, NodeInput, EdgeInput
from graphene.types.generic import GenericScalar

from arkitekt.schema import Node as ApiNode, template
from arkitekt.schema import NodeType
from arkitekt.schema import Template as ApiTemplate
import namegenerator

logger = logging.getLogger(__name__)


class Draw(BalderMutation):
    class Arguments:
        name = graphene.String(required=True)
        graph = graphene.Argument(GraphInput, required=True)

    @bounced(anonymous=False)
    def mutate(root, info, name, graph):
        flow = models.Flow.objects.create(
            graph=graph, name=name, creator=info.context.user
        )
        return flow

    class Meta:
        type = types.Flow
        operation = "makeflow"


class UpdateFlow(BalderMutation):
    class Arguments:
        id = graphene.ID(required=True)
        graph = graphene.Argument(GraphInput, required=True)

    @bounced(anonymous=False)
    def mutate(root, info, id, graph):

        flow = models.Flow.objects.get(id=id)
        flow.graph = graph
        flow.save()

        return flow

    class Meta:
        type = types.Flow
        operation = "updateflow"


class DrawVanilla(BalderMutation):
    class Arguments:
        name = graphene.String(required=True)

    @bounced(anonymous=False)
    def mutate(
        root,
        info,
        name,
    ):

        nodes = [
            {
                "id": "1",
                "typename": "ArgNode",
                "instream": [[]],
                "outstream": [[]],
                "constream": [[]],
                "position": {"x": 0, "y": 50},
            },
            {
                "id": "2",
                "typename": "ReturnNode",
                "instream": [[]],
                "outstream": [[]],
                "constream": [[]],
                "position": {"x": 1500, "y": 50},
            },
            {
                "id": "3",
                "typename": "KwargNode",
                "instream": [[]],
                "outstream": [[]],
                "constream": [[]],
                "position": {"x": 750, "y": 100},
            },
        ]

        flow = models.Flow.objects.create(
            graph={"nodes": nodes, "edges": [], "globals": []},
            name=name,
            creator=info.context.user,
        )
        return flow

    class Meta:
        type = types.Flow
        operation = "drawvanilla"


class DeleteFlowReturn(graphene.ObjectType):
    id = graphene.ID()


class DeleteFlow(BalderMutation):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def mutate(root, info, id=None):

        graph = models.Flow.objects.get(id=id)
        graph.delete()
        return {"id": id}

    class Meta:
        type = DeleteFlowReturn

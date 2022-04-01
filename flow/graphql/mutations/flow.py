from email.policy import default
from balder.types import BalderMutation
import graphene
from flow import models, types
from lok import bounced
import logging
from flow.inputs import NodeInput, EdgeInput
from graphene.types.generic import GenericScalar

from arkitekt.schema import Node as ApiNode, template
from arkitekt.schema import NodeType
from arkitekt.schema import Template as ApiTemplate
import namegenerator

logger = logging.getLogger(__name__)


class Draw(BalderMutation):
    class Arguments:
        name = graphene.String(required=True)
        nodes = graphene.List(NodeInput)
        edges = graphene.List(EdgeInput)

    @bounced(anonymous=False)
    def mutate(root, info, name, nodes=[], edges=[]):
        flow = models.Flow.objects.create(
            edges=edges, nodes=nodes, name=name, creator=info.context.user
        )
        return flow

    class Meta:
        type = types.Flow
        operation = "makeflow"


class UpdateFlow(BalderMutation):
    class Arguments:
        id = graphene.ID(required=True)
        nodes = graphene.List(NodeInput)
        edges = graphene.List(EdgeInput)

    @bounced(anonymous=False)
    def mutate(root, info, id, nodes=[], edges=[]):

        flow = models.Flow.objects.get(id=id)
        flow.edges = edges
        flow.nodes = nodes
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
                "type": "ArgNode",
                "args": [],
                "returns": [],
                "kwargs": [],
                "position": {"x": 0, "y": 50},
            },
            {
                "id": "2",
                "type": "ReturnNode",
                "args": [],
                "returns": [],
                "kwargs": [],
                "position": {"x": 1500, "y": 50},
            },
            {
                "id": "3",
                "type": "KwargNode",
                "args": [],
                "returns": [],
                "kwargs": [],
                "position": {"x": 750, "y": 100},
            },
        ]

        flow = models.Flow.objects.create(
            edges=[], nodes=nodes, name=name, creator=info.context.user
        )
        return flow

    class Meta:
        type = types.Flow
        operation = "drawvanilla"

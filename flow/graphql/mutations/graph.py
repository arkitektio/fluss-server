from balder.types import BalderMutation
import graphene
from flow import models, types
from lok import bounced
import logging
from flow.diagram import Diagram, ArgNode, KwargNode, ReturnNode, ArkitektNode, ArkitektType, ArgData, KwargData, ReturnData
from graphene.types.generic import GenericScalar

from arkitekt.schema import Node as ApiNode
from arkitekt.schema import NodeType
from arkitekt.schema import Template as ApiTemplate
logger = logging.getLogger(__name__)




class Deploy(BalderMutation):

    class Arguments:
        graph = graphene.ID(description="The graph we will use to create a template", required=False)

    @bounced(anonymous=False)
    def mutate(root, info, *args, graph=None):
        graph = models.Graph.objects.get(id=graph)
        # Request PortTemplate from arkitekt
        
        diagram = Diagram(**graph.diagram)
        logger.info(diagram)

        argNodes = [value for value in diagram.elements if isinstance(value, ArgNode) ]
        kwargNodes = [value for value in diagram.elements if isinstance(value, KwargNode) ]
        returnNodes = [value for value in diagram.elements if isinstance(value, ReturnNode) ]

        assert len(list(zip(argNodes, kwargNodes, returnNodes))) == 1, "You cannot have more then one of the argNodes, KwargNode, and ReturnNodes to deploy"

        argData = argNodes[0].data
        kwargData = kwargNodes[0].data
        returnData = returnNodes[0].data

        arkitektNodes = [value for value in diagram.elements if isinstance(value, ArkitektNode)]
        # A Graph that contains generators is always a generator??? Maybe stupid but for now the solution
        logger.info(arkitektNodes)
        gen_nodes = [node for node in arkitektNodes if node.data.node.type == ArkitektType.GENERATOR]
        logger.info(f"Contains gennodes {gen_nodes}")
        node_type = NodeType.GENERATOR if len(gen_nodes) != 0 else NodeType.FUNCTION

        logger.info(node_type)

        arkitekt_node = ApiNode.objects.create(**{
            "name": graph.name,
            "args": [p.dict() for p in argData.args],
            "kwargs": [p.dict() for p in kwargData.kwargs],
            "returns": [p.dict() for p in returnData.returns],
            "description": "No Description Yet",
            "type": node_type.value,
            "package": "fluss",
            "interface": graph.name,
        })

        logger.info(arkitekt_node)

        arkitekt_node_id = arkitekt_node.id
        arkitekt_node_name = arkitekt_node.name
        node, created = models.FlowNode.objects.get_or_create(arkitekt_id=arkitekt_node_id, defaults={"name": arkitekt_node_name})
        graph.node = node
        graph.save()


        arkitekt_template = ApiTemplate.objects.create(**{
                "node": graph.node.arkitekt_id,
                "params": {
                    "fluss": True
                },
                "extensions": ["graph"],
                "version": "main"
        })

        logger.info(arkitekt_template)

        template, created = models.FlowTemplate.objects.get_or_create(arkitekt_id=arkitekt_template.id)
        graph.template = template         
        graph.save()

        return graph

    class Meta:
        type = types.Graph


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




class UpdateGraph(BalderMutation):

    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")
        diagram = GenericScalar(description="The Graph")

    @bounced(anonymous=False)
    def mutate(root, info, id=None, diagram=None):

        graph = models.Graph.objects.get(id=id)
        graph.diagram = diagram
        graph.save()

        return graph

    class Meta:
        type = types.Graph



class CreateGraph(BalderMutation):

    class Arguments:
        name = graphene.String(description="The name of this graph", required=False)

    @bounced(anonymous=False)
    def mutate(root, info, *args, name=None):

        #TODO: Implement creating graph through node
        graph = models.Graph.objects.create(
            creator = info.context.user,
            name = name
        )

        return graph

    class Meta:
        type = types.Graph
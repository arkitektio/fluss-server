from flow.diagram import ArgData, ArkitektData, Diagram, KwargData, Node, ReturnData
from typing import List, Optional, Union
from django.http import request
from balder.types import BalderQuery, BalderMutation
from flow import types
from flow import models
import graphene
from herre import bounced
from graphene.types.generic import GenericScalar
import requests
import namegenerator
from delt.bridge import arkitekt
from pydantic import BaseModel
from enum import Enum


createNodeMutation = """
                mutation($description: String,
                $name: String!,
                $args: [ArgPortInput],
                $kwargs: [KwargPortInput],
                $returns: [ReturnPortInput],
                $type: NodeTypeInput,
                $interface: String!
                $package: String!
                ) {
                    createNode(
                        description: $description,
                        name: $name,
                        args: $args,
                        kwargs: $kwargs,
                        returns: $returns,
                        type: $type,
                        interface: $interface,
                        package: $package
                    ){
                        id
                        name
                    }
                }
            """

    
createTemplateMutation = """
    mutation($node: ID!, $params: GenericScalar) {
        createTemplate(node: $node, params: $params){
            id
        }
    }
"""



class Deploy(BalderMutation):

    class Arguments:
        graph = graphene.ID(description="The graph we will use to create a template", required=False)

    @bounced(anonymous=False)
    def mutate(root, info, *args, graph=None):
        graph = models.Graph.objects.get(id=graph)
        token = info.context.bounced.token
        # Request PortTemplate from arkitekt
        if not graph.node:

            diagram = Diagram(**graph.diagram)

            argNodes = [value for value in diagram.elements if value.type == "argNode" ]
            kwargNodes = [value for value in diagram.elements if value.type == "kwargNode" ]
            returnNodes = [value for value in diagram.elements if value.type == "returnNode" ]
            assert len(list(zip(argNodes, kwargNodes, returnNodes))) == 1, "You cannot have more then one of the argNodes, KwargNode, and ReturnNodes to deploy"

            argData: ArgData = argNodes[0].data
            kwargData: KwargData = kwargNodes[0].data
            returnData: ReturnData = returnNodes[0].data

            arkitektNodes = [value for value in diagram.elements if isinstance(value, Node) and isinstance(value.data, ArkitektData)]
            print(arkitektNodes)


            answer = arkitekt.call(createNodeMutation, {
                "name": namegenerator.gen(),
                "args": [p.dict() for p in argData.args],
                "kwargs": [p.dict() for p in kwargData.kwargs],
                "returns": [p.dict() for p in returnData.returns],
                "type": "FUNCTION",
                "package": "fluss",
                "interface": namegenerator.gen(),
            })

            print("Created node", answer)
            arkitekt_node_id = answer["createNode"]["id"]
            arkitekt_node_name = answer["createNode"]["id"]
            node, created = models.FlowNode.objects.get_or_create(arkitekt_id=arkitekt_node_id, defaults={"name": arkitekt_node_name})
            graph.node = node
            graph.save()


        answer = arkitekt.call(createTemplateMutation, {
                "node": graph.node.arkitekt_id,
                "params": {
                    "fluss": True
                }
        })

        print(answer)

        arkitekt_template_id = answer["createTemplate"]["id"]

        template, created = models.FlowTemplate.objects.get_or_create(arkitekt_id=arkitekt_template_id)
        graph.template = template         
        graph.save()

        return graph

    class Meta:
        type = types.Graph



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
        node = graphene.ID(description="Use node as template?", required=False)

    @bounced(anonymous=False)
    def mutate(root, info, *args, node=None):

        #TODO: Implement creating graph through node
        graph = models.Graph.objects.create(
            creator = info.context.user
        )

        return graph

    class Meta:
        type = types.Graph





class GraphDetail(BalderQuery):

    class Arguments:
        id = graphene.ID(description="A unique ID for this Graph")
        template = graphene.ID(description="The corresponding template on arkitekt (proxied through FlowTemplate)")


    @bounced()
    def resolve(root, info , *args,  id=None, template=None):
        if template: return models.Graph.objects.get(template__arkitekt_id=template)
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


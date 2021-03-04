from django.http import request
from balder.types import BalderQuery, BalderMutation
from flow import types
from flow import models
import graphene
from herre import bounced
from graphene.types.generic import GenericScalar
import requests
import namegenerator

class Deploy(BalderMutation):

    class Arguments:
        graph = graphene.ID(description="The graph we will use to create a template", required=False)

    @bounced(anonymous=False)
    def mutate(root, info, *args, graph=None):

        #TODO: Use diagram and create a template over at the api

        # Request PortTemplate from arkitekt


        createNodeMutation = """
            mutation($description: String,
             $name: String!,
             $outputs: [OutPortInput],
             $inputs: [InPortInput],
             $type: NodeTypeInput,
             $interface: String!
             $package: String!
             ) {
                createNode(
                    description: $description,
                    name: $name,
                    outputs: $outputs,
                    inputs: $inputs,
                    type: $type,
                    interface: $interface,
                    package: $package
                ){
                    id
                }
            }


        """

        result = requests.post("http://arkitekt:8090/graphql", json={"query": createNodeMutation, "variables": {
            "name": namegenerator.gen(),
            "inputs": [],
            "outputs": [],
            "type": "FUNCTION",
            "package": "fluss",
            "interface": namegenerator.gen(),
        }})

        answer = result.json()
        print("Created node", answer)
        node = answer["data"]["createNode"]["id"]



        createPortTemplateMutation = """
            mutation($q: String!, $node: ID!, $env: GenericScalar) {
                createPort(q: $q, env: $env, node: $node){
                    arkitektId
                    id
                }
            }
        """

        result = requests.post("http://port:8060/graphql", json={"query": createPortTemplateMutation, "variables": {
            "q": "jhnnsrs/flowly:latest",
            "node": node,
            "env": {
                "FLUSS": "fluss",
                "GRAPH": "graph",
            }
        }})

        answer = result.json()
        print(answer)

        arkitekt_id = answer["data"]["createPort"]["arkitektId"]
        port_id = answer["data"]["createPort"]["id"]

        model, created = models.Template.objects.get_or_create(arkitekt_id=arkitekt_id,port_id=port_id)

        return model

    class Meta:
        type = types.Template



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


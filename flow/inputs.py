import graphene
from graphene.types.generic import GenericScalar


class FlowArgInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    label = graphene.String()
    name = graphene.String()
    typename = graphene.String()
    description = graphene.String()


class FlowKwargInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    label = graphene.String()
    name = graphene.String()
    typename = graphene.String()
    description = graphene.String()


class FlowReturnInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    label = graphene.String()
    name = graphene.String()
    typename = graphene.String()
    description = graphene.String()


class PositionInput(graphene.InputObjectType):
    x = graphene.Float(required=True)
    y = graphene.Float(required=True)


class StreamItemInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    type = graphene.String(required=True)


class NodeInput(graphene.InputObjectType):
    id = graphene.String(required=True)
    typename = graphene.String(required=True)
    package = graphene.String(required=False)
    name = graphene.String(required=False)
    description = graphene.String(required=False)
    interface = graphene.String(required=False)
    kind = graphene.String()
    implementation = graphene.String(required=False)
    position = graphene.Field(PositionInput, required=True)
    extra = GenericScalar(required=False)
    instream = graphene.List(
        graphene.List(StreamItemInput, required=True), required=True
    )
    outstream = graphene.List(
        graphene.List(StreamItemInput, required=True), required=True
    )
    constream = graphene.List(
        graphene.List(StreamItemInput, required=True), required=True
    )


class EdgeInput(graphene.InputObjectType):
    id = graphene.String(required=True)
    typename = graphene.String(required=True)
    source = graphene.String(required=True)
    target = graphene.String(required=True)
    sourceHandle = graphene.String(required=True)
    targetHandle = graphene.String(required=True)
    label = graphene.String(required=False)


class GlobalInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    value = GenericScalar()


class GraphInput(graphene.InputObjectType):
    zoom = graphene.Float(required=False)
    nodes = graphene.List(NodeInput, required=True)
    edges = graphene.List(EdgeInput, required=True)
    globals = graphene.List(GlobalInput, required=True)

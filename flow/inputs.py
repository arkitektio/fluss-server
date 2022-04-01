import graphene
from graphene.types.generic import GenericScalar


class FlowArgInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    label = graphene.String()
    name = graphene.String()
    type = graphene.String()
    description = graphene.String()


class FlowKwargInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    label = graphene.String()
    name = graphene.String()
    type = graphene.String()
    description = graphene.String()


class FlowReturnInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    label = graphene.String()
    name = graphene.String()
    type = graphene.String()
    description = graphene.String()


class PositionInput(graphene.InputObjectType):
    x = graphene.Float(required=True)
    y = graphene.Float(required=True)


class NodeInput(graphene.InputObjectType):
    id = graphene.String(required=True)
    type = graphene.String(required=True)
    args = graphene.List(FlowArgInput)
    kwargs = graphene.List(FlowKwargInput)
    returns = graphene.List(FlowReturnInput)
    package = graphene.String(required=False)
    name = graphene.String(required=False)
    description = graphene.String(required=False)
    interface = graphene.String(required=False)
    kind = graphene.String()
    implementation = graphene.String(required=False)
    position = graphene.Field(PositionInput, required=True)
    extra = GenericScalar(required=False)


class EdgeInput(graphene.InputObjectType):
    id = graphene.String(required=True)
    type = graphene.String(required=True)
    source = graphene.String(required=True)
    target = graphene.String(required=True)
    sourceHandle = graphene.String()
    targetHandle = graphene.String()
    label = graphene.String(required=False)

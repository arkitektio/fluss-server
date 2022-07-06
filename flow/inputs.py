import graphene
from graphene.types.generic import GenericScalar
from flow.enums import EventTypeInput
from flow.scalars import EventValue


class PositionInput(graphene.InputObjectType):
    x = graphene.Float(required=True)
    y = graphene.Float(required=True)


class StreamType(graphene.Enum):
    INT = "INT"
    STRING = "STRING"
    STRUCTURE = "STRUCTURE"
    LIST = "LIST"
    BOOL = "BOOL"
    ENUM = "ENUM"
    DICT = "DICT"
    UNSET = "UNSET"


class StreamItemInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    type = StreamType(required=True)
    identifier = graphene.String(required=False)


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
    stream = graphene.List(StreamItemInput, required=False)


class GlobalInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    value = GenericScalar()


class GraphInput(graphene.InputObjectType):
    zoom = graphene.Float(required=False)
    nodes = graphene.List(NodeInput, required=True)
    edges = graphene.List(EdgeInput, required=True)
    globals = graphene.List(GlobalInput, required=True)


class RunEventInput(graphene.InputObjectType):
    handle = graphene.String(required=True)
    type = EventTypeInput(required=True)
    source = graphene.String(required=True)
    value = EventValue(required=False)

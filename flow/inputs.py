import graphene
from graphene.types.generic import GenericScalar
from flow.enums import EventTypeInput
from flow.scalars import Any, EventValue


class PositionInput(graphene.InputObjectType):
    x = graphene.Float(required=True)
    y = graphene.Float(required=True)


class StreamKind(graphene.Enum):
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
    kind = StreamKind(required=True)
    identifier = graphene.String(required=False)


class ChildPortInput(graphene.InputObjectType):
    identifier = graphene.String(description="The identifier")
    kind = StreamKind(description="The type of this argument", required=True)


class WidgetInput(graphene.InputObjectType):
    query = graphene.String()
    kind = graphene.String(description="The typename of the widget", required=True)


class PortInput(graphene.InputObjectType):
    identifier = graphene.String(description="The identifier")
    key = graphene.String(description="The key of the arg", required=True)
    name = graphene.String(description="The name of this argument")
    label = graphene.String(description="The name of this argument")
    default = Any(description="The default value of this port", required=False)
    kind = StreamKind(description="The type of this argument", required=True)
    description = graphene.String(description="The description of this argument")
    child = graphene.Field(ChildPortInput, description="The child of this argument")
    widget = graphene.Field(WidgetInput, description="The child of this argument")


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
    defaults = GenericScalar(required=False)
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
    args = graphene.List(PortInput, required=True)
    kwargs = graphene.List(PortInput, required=True)
    returns = graphene.List(PortInput, required=True)
    globals = graphene.List(GlobalInput, required=True)


class RunEventInput(graphene.InputObjectType):
    handle = graphene.String(required=True)
    type = EventTypeInput(required=True)
    source = graphene.String(required=True)
    value = EventValue(required=False)

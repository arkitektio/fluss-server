import graphene
from graphene.types.generic import GenericScalar
from flow.enums import EventTypeInput, ReactiveImplementation, MapStrategy
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


class StreamItemChildInput(graphene.InputObjectType):
    kind = StreamKind(required=True)
    identifier = graphene.String(required=False)
    child = graphene.Field(lambda: StreamItemChildInput, required=False)


class StreamItemInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    kind = StreamKind(required=True)
    identifier = graphene.String(required=False)
    nullable = graphene.Boolean(required=True)
    child = graphene.Field(StreamItemChildInput, required=False)


class ChildPortInput(graphene.InputObjectType):
    nullable = graphene.Boolean(required=False)
    identifier = graphene.String(description="The identifier")
    kind = StreamKind(description="The type of this argument", required=True)
    child = graphene.Field(lambda: ChildPortInput, required=False)


class ChoiceInput(graphene.InputObjectType):
    value = Any(required=True)
    label = graphene.String(required=True)


class WidgetInput(graphene.InputObjectType):
    kind = graphene.String(description="type", required=True)
    query = graphene.String(description="Do we have a possible")
    dependencies = graphene.List(
        graphene.String, description="The dependencies of this port"
    )
    choices = graphene.List(ChoiceInput, description="The dependencies of this port")
    max = graphene.Int(description="Max value for int widget")
    min = graphene.Int(description="Max value for int widget")
    placeholder = graphene.String(description="Placeholder for any widget")
    as_paragraph = graphene.Boolean(description="Is this a paragraph")
    hook = graphene.String(description="A hook for the app to call")
    ward = graphene.String(description="A ward for the app to call")


class ReturnWidgetInput(graphene.InputObjectType):
    kind = graphene.String(description="type", required=True)
    query = graphene.String(description="Do we have a possible")
    hook = graphene.String(description="A hook for the app to call")
    ward = graphene.String(description="A ward for the app to call")


class ArgPortInput(graphene.InputObjectType):
    identifier = graphene.String(description="The identifier")
    key = graphene.String(description="The key of the arg", required=True)
    name = graphene.String(description="The name of this argument")
    label = graphene.String(description="The name of this argument")
    kind = StreamKind(description="The type of this argument", required=True)
    description = graphene.String(description="The description of this argument")
    child = graphene.Field(ChildPortInput, description="The child of this argument")
    widget = graphene.Field(WidgetInput, description="The child of this argument")
    default = Any(description="The key of the arg", required=False)
    nullable = graphene.Boolean(description="Is this argument nullable", required=True)


class ReturnPortInput(graphene.InputObjectType):
    identifier = graphene.String(description="The identifier")
    key = graphene.String(description="The key of the arg", required=True)
    name = graphene.String(description="The name of this argument")
    label = graphene.String(description="The name of this argument")
    kind = StreamKind(description="The type of this argument", required=True)
    description = graphene.String(description="The description of this argument")
    child = graphene.Field(ChildPortInput, description="The child of this argument")
    widget = graphene.Field(ReturnWidgetInput, description="The child of this argument")
    nullable = graphene.Boolean(description="Is this argument nullable", required=True)


class ReserveParamsInput(graphene.InputObjectType):
    agents = graphene.List(graphene.String, required=False)

class NodeInput(graphene.InputObjectType):
    id = graphene.String(required=True)
    typename = graphene.String(required=True)
    hash = graphene.String(required=False)
    interface = graphene.String(required=False) # for template nodes
    name = graphene.String(required=False)
    description = graphene.String(required=False)
    kind = graphene.String()
    implementation = graphene.Field(ReactiveImplementation, required=False)
    documentation = graphene.String(required=False)
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
    map_strategy = graphene.Argument(MapStrategy, required=False)
    allow_local = graphene.Boolean(required=False)
    reserve_params = graphene.Argument(ReserveParamsInput, required=False)



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
    args = graphene.List(ArgPortInput, required=True)
    returns = graphene.List(ReturnPortInput, required=True)
    globals = graphene.List(GlobalInput, required=True)


class RunEventInput(graphene.InputObjectType):
    handle = graphene.String(required=True)
    type = EventTypeInput(required=True)
    source = graphene.String(required=True)
    value = EventValue(required=False)

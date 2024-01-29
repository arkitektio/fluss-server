import graphene
from graphene.types.generic import GenericScalar
from flow.enums import EventTypeInput, ReactiveImplementation, MapStrategy, Scope
from flow.scalars import Any, EventValue


class PositionInput(graphene.InputObjectType):
    x = graphene.Float(required=True)
    y = graphene.Float(required=True)


class StreamKind(graphene.Enum):
    INT = "INT"
    STRING = "STRING"
    STRUCTURE = "STRUCTURE"
    FLOAT = "FLOAT"
    LIST = "LIST"
    BOOL = "BOOL"
    ENUM = "ENUM"
    DICT = "DICT"
    UNION = "UNION"
    UNSET = "UNSET"


class StreamItemChildInput(graphene.InputObjectType):
    kind = StreamKind(required=True)
    scope = graphene.Argument(
        Scope, description="The scope of this argument", required=True
    )
    identifier = graphene.String(required=False)
    nullable = graphene.Boolean(required=True)
    variants = graphene.List(lambda: StreamItemChildInput, required=False)
    child = graphene.Field(lambda: StreamItemChildInput, required=False)


class StreamItemInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    kind = StreamKind(required=True)
    scope = graphene.Argument(
        Scope, description="The scope of this argument", required=True
    )
    identifier = graphene.String(required=False)
    nullable = graphene.Boolean(required=True)
    variants = graphene.List(lambda: StreamItemChildInput, required=False)
    child = graphene.Field(StreamItemChildInput, required=False)


class ChoiceInput(graphene.InputObjectType):
    value = Any(required=True)
    label = graphene.String(required=True)
    description = graphene.String(required=False)


class WidgetInput(graphene.InputObjectType):
    kind = graphene.String(description="type", required=True)
    query = graphene.String(description="Do we have a possible")
    dependencies = graphene.List(
        graphene.String, description="The dependencies of this port"
    )
    choices = graphene.List(ChoiceInput, description="The dependencies of this port")
    max = graphene.Float(description="Max value for int widget")
    min = graphene.Float(description="Max value for int widget")
    step = graphene.Float(description="Max value for int widget")
    placeholder = graphene.String(description="Placeholder for any widget")
    as_paragraph = graphene.Boolean(description="Is this a paragraph")
    hook = graphene.String(description="A hook for the app to call")
    ward = graphene.String(description="A ward for the app to call")


class ReturnWidgetInput(graphene.InputObjectType):
    kind = graphene.String(description="type", required=True)
    query = graphene.String(description="Do we have a possible")
    choices = graphene.List(ChoiceInput, description="The dependencies of this port")
    hook = graphene.String(description="A hook for the app to call")
    ward = graphene.String(description="A ward for the app to call")


class ChildPortInput(graphene.InputObjectType):
    nullable = graphene.Boolean(required=False)
    scope = graphene.Argument(
        Scope, description="The scope of this argument", required=True
    )
    identifier = graphene.String(description="The identifier")
    kind = StreamKind(description="The type of this argument", required=True)
    child = graphene.Field(lambda: ChildPortInput, required=False)
    variants = graphene.List(lambda: ChildPortInput, required=False)
    assign_widget = graphene.Field(WidgetInput, description="Description of the Widget")
    return_widget = graphene.Field(ReturnWidgetInput, description="A return widget")


class ChoiceInput(graphene.InputObjectType):
    value = Any(required=True)
    label = graphene.String(required=True)


class PortInput(graphene.InputObjectType):
    identifier = graphene.String(description="The identifier")
    key = graphene.String(description="The key of the arg", required=True)
    name = graphene.String(description="The name of this argument")
    label = graphene.String(description="The name of this argument")
    kind = StreamKind(description="The type of this argument", required=True)
    scope = graphene.Argument(
        Scope, description="The scope of this argument", required=True
    )
    description = graphene.String(description="The description of this argument")
    child = graphene.Field(ChildPortInput, description="The child of this argument")
    variants = graphene.List(lambda: ChildPortInput, required=False)
    assign_widget = graphene.Field(
        WidgetInput, description="The child of this argument"
    )
    return_widget = graphene.Field(
        ReturnWidgetInput, description="The child of this argument"
    )
    default = Any(description="The key of the arg", required=False)
    nullable = graphene.Boolean(description="Is this argument nullable", required=True)


class BindsInput(graphene.InputObjectType):
    templates = graphene.List(graphene.String, required=False)
    clients = graphene.List(graphene.String, required=False)


class NodeInput(graphene.InputObjectType):
    id = graphene.String(required=True)
    typename = graphene.String(required=True)
    hash = graphene.String(required=False)
    interface = graphene.String(required=False)  # for template nodes
    name = graphene.String(required=False)
    description = graphene.String(required=False)
    kind = graphene.String()
    implementation = graphene.Field(ReactiveImplementation, required=False)
    position = graphene.Field(PositionInput, required=True)
    defaults = GenericScalar(required=False)
    extra = GenericScalar(required=False)
    instream = graphene.List(graphene.List(PortInput, required=True), required=True)
    outstream = graphene.List(graphene.List(PortInput, required=True), required=True)
    constream = graphene.List(graphene.List(PortInput, required=True), required=True)
    map_strategy = graphene.Argument(MapStrategy, required=False)
    allow_local = graphene.Boolean(required=False)
    binds = graphene.Argument(BindsInput, required=False)
    assign_timeout = graphene.Float(required=False, default_value=100000)
    yield_timeout = graphene.Float(required=False, default_value=100000)
    max_retries = graphene.Int(required=False, default_value=3)
    retry_delay = graphene.Int(required=False, default_value=5000)
    reserve_timeout = graphene.Float(required=False, default_value=100000)
    parent_node = graphene.ID(required=False)


class EdgeInput(graphene.InputObjectType):
    id = graphene.String(required=True)
    typename = graphene.String(required=True)
    source = graphene.String(required=True)
    target = graphene.String(required=True)
    sourceHandle = graphene.String(required=True)
    targetHandle = graphene.String(required=True)
    stream = graphene.List(StreamItemInput, required=False)


class GlobalInput(graphene.InputObjectType):
    to_keys = graphene.List(graphene.String, required=True)
    port = graphene.Field(PortInput, required=True)


class GraphInput(graphene.InputObjectType):
    zoom = graphene.Float(required=False)
    nodes = graphene.List(NodeInput, required=True)
    edges = graphene.List(EdgeInput, required=True)
    args = graphene.List(PortInput, required=True)
    returns = graphene.List(PortInput, required=True)
    globals = graphene.List(GlobalInput, required=True)


class RunEventInput(graphene.InputObjectType):
    handle = graphene.String(required=True)
    type = EventTypeInput(required=True)
    source = graphene.String(required=True)
    value = EventValue(required=False)
    caused_by = graphene.List(graphene.Int, required=True)

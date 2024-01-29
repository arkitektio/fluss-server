from balder.types import BalderObject
from flow import models
from django.contrib.auth import get_user_model
import graphene
from graphene.types.generic import GenericScalar
from balder.registry import register_type
from flow.inputs import StreamKind
from flow.scalars import Any, EventValue
from flow.enums import ReactiveImplementation, MapStrategy, Scope, ContractStatus


class PinnableMixin:
    pinned = graphene.Boolean(default_value=False)

    def resolve_pinned(root, info, *args, **kwargs):
        return root.pinned_by.filter(id=info.context.user.id).exists()


class Position(graphene.ObjectType):
    x = graphene.Int(required=True)
    y = graphene.Int(required=True)


class User(BalderObject):
    class Meta:
        model = get_user_model()


class Deployed(graphene.ObjectType):
    status = graphene.String(default_value="Ok")


class FlowElement(graphene.Interface):
    id = graphene.String()

    @classmethod
    def resolve_type(cls, instance, info):
        if "source" in instance:
            return FlowEdge
        else:
            return FlowNode


class FlowArg(graphene.ObjectType):
    key = graphene.String(required=True)

    label = graphene.String()
    name = graphene.String()
    typename = graphene.String()
    description = graphene.String()


class FlowKwarg(graphene.ObjectType):
    key = graphene.String(required=True)
    label = graphene.String()
    name = graphene.String()
    typename = graphene.String()
    description = graphene.String()


class FlowReturn(graphene.ObjectType):
    key = graphene.String(required=True)
    label = graphene.String()
    name = graphene.String()
    typename = graphene.String()
    description = graphene.String()


class FlowNode(graphene.Interface):
    id = graphene.String(required=True)
    position = graphene.Field(Position, required=True)
    parent_node = graphene.Field(graphene.ID, required=False)
    typename = graphene.String(required=True)

    @classmethod
    def resolve_type(cls, instance, info):
        if instance["typename"] == "ArkitektNode":
            return ArkitektNode
        if instance["typename"] == "ArkitektFilterNode":
            return ArkitektFilterNode
        if instance["typename"] == "ReactiveNode":
            return ReactiveNode
        if instance["typename"] == "ArgNode":
            return ArgNode
        if instance["typename"] == "KwargNode":
            return KwargNode
        if instance["typename"] == "LocalNode":
            return LocalNode
        if instance["typename"] == "ReturnNode":
            return ReturnNode
        if instance["typename"] == "GraphNode":
            return GraphNode


class StreamItemChild(graphene.ObjectType):
    kind = StreamKind(required=True)
    scope = Scope(required=True)
    nullable = graphene.Boolean(required=True)
    identifier = graphene.String(required=False)
    child = graphene.Field(lambda: StreamItemChild, required=False)
    variants = graphene.List(lambda: StreamItemChild, required=False)

    def resolve_scope(self, info):
        return self.get("scope", Scope.GLOBAL)

    def resolve_nullable(self, info):
        return self.get("nullable", False)


class Choice(graphene.ObjectType):
    value = Any(required=True)
    label = graphene.String(required=True)
    description = graphene.String(required=False)


class Widget(graphene.ObjectType):
    kind = graphene.String(description="type", required=True)
    query = graphene.String(description="Do we have a possible")
    dependencies = graphene.List(
        graphene.String, description="The dependencies of this port"
    )
    choices = graphene.List(Choice, description="The dependencies of this port")
    max = graphene.Float(description="Max value for int widget")
    min = graphene.Float(description="Max value for int widget")
    step = graphene.Float(description="Max value for int widget")
    placeholder = graphene.String(description="Placeholder for any widget")
    as_paragraph = graphene.Boolean(description="Is this a paragraph")
    hook = graphene.String(description="A hook for the app to call")
    ward = graphene.String(description="A hook for the app to call")


class ReturnWidget(graphene.ObjectType):
    kind = graphene.String(description="type", required=True)
    query = graphene.String(description="The graphql query for this port")
    dependencies = graphene.List(
        graphene.String, description="The dependencies of this port"
    )
    choices = graphene.List(Choice, description="The dependencies of this port")


class StreamItem(graphene.ObjectType):
    key = graphene.String(required=True)
    kind = StreamKind(required=True)
    scope = Scope(required=True)
    identifier = graphene.String(required=False)
    nullable = graphene.Boolean(required=True)
    child = graphene.Field(StreamItemChild, required=False)
    variants = graphene.List(StreamItemChild, required=False)

    def resolve_scope(self, info):
        return self.get("scope", Scope.GLOBAL)

    def resolve_nullable(self, info):
        return self.get("nullable", False)


class PortChild(graphene.ObjectType):
    nullable = graphene.Boolean(required=True)
    kind = StreamKind(required=True)
    scope = Scope(required=True)
    identifier = graphene.String(required=False)
    variants = graphene.List(lambda: PortChild, required=False)
    child = graphene.Field(lambda: PortChild, required=False)
    assign_widget = graphene.Field(Widget, description="Description of the Widget")
    return_widget = graphene.Field(ReturnWidget, description="A return widget")

    def resolve_scope(self, info):
        return self.get("scope", Scope.GLOBAL)

    def resolve_nullable(self, info):
        return self.get("nullable", False)


class Port(graphene.ObjectType):
    key = graphene.String(required=True)
    nullable = graphene.Boolean(description="The key of the arg", required=True)
    scope = Scope(required=True)
    default = Any(required=False)
    label = graphene.String()
    identifier = graphene.String()
    variants = graphene.List(lambda: PortChild, required=False)
    kind = StreamKind(required=True)
    child = graphene.Field(PortChild, required=False)
    label = graphene.String()
    description = graphene.String()
    assign_widget = graphene.Field(Widget)
    return_widget = graphene.Field(ReturnWidget)

    def resolve_scope(self, info):
        return self.get("scope", Scope.GLOBAL)


class FlowNodeCommons(graphene.Interface):
    name = graphene.String(required=True)
    instream = graphene.List(graphene.List(Port, required=True), required=True)
    outstream = graphene.List(graphene.List(Port, required=True), required=True)
    constream = graphene.List(graphene.List(Port, required=True), required=True)
    constants = GenericScalar()
    description = graphene.String(required=True)
    defaults = GenericScalar()

    def resolve_name(self, info):
        return self.get("name", "")

    def resolve_description(self, info):
        return self.get("description", "No description")


class RetriableNode(graphene.Interface):
    max_retries = graphene.Int(required=True)
    retry_delay = graphene.Int(required=True)

    def resolve_max_retries(self, info):
        return self.get("max_retries", 0)

    def resolve_retry_delay(self, info):
        return self.get("retry_delay", 1000)


class Binds(graphene.ObjectType):
    templates = graphene.List(graphene.String, required=False)
    clients = graphene.List(graphene.String, required=False)


@register_type
class ArkitektNode(graphene.ObjectType):
    """A map node that utilizes
    a call to the associated rekuest node
    run a task
    """

    hash = graphene.String(required=True)
    kind = graphene.String(required=True)
    map_strategy = graphene.Field(MapStrategy, required=True)
    allow_local = graphene.Boolean(required=True)
    assign_timeout = graphene.Float(required=True)
    yield_timeout = graphene.Float(required=True)
    reserve_timeout = graphene.Float(required=True)
    binds = graphene.Field(Binds, required=False)

    class Meta:
        interfaces = (FlowNode, FlowNodeCommons, RetriableNode)


@register_type
class ArkitektFilterNode(graphene.ObjectType):
    """A filter node that utilizes
    a call to the associated rekuest node
    to filter a stream based on a predicate
    (the rekuest node must return a boolean)
    """

    hash = graphene.String(required=True)
    kind = graphene.String(required=True)
    map_strategy = graphene.Field(MapStrategy, required=True)
    allow_local = graphene.Boolean(required=True)
    assign_timeout = graphene.Float(required=True)
    yield_timeout = graphene.Float(required=True)
    reserve_timeout = graphene.Float(required=True)
    binds = graphene.Field(Binds, required=False)

    class Meta:
        interfaces = (FlowNode, FlowNodeCommons, RetriableNode)


@register_type
class LocalNode(graphene.ObjectType):
    hash = graphene.String(required=True)
    interface = graphene.String(required=True)
    kind = graphene.String(required=True)
    defaults = GenericScalar(required=False)
    map_strategy = graphene.Field(MapStrategy, required=True)
    allow_local = graphene.Boolean(required=True)
    assign_timeout = graphene.Float(required=True)
    yield_timeout = graphene.Float(required=True)
    retry_sleep_ms = graphene.Int(required=True)

    class Meta:
        interfaces = (FlowNode, FlowNodeCommons, RetriableNode)


@register_type
class GraphNode(graphene.ObjectType):
    hash = graphene.String(required=True)

    class Meta:
        interfaces = (FlowNode, FlowNodeCommons)


@register_type
class ArgNode(graphene.ObjectType):
    class Meta:
        interfaces = (FlowNode, FlowNodeCommons)


@register_type
class KwargNode(graphene.ObjectType):
    class Meta:
        interfaces = (FlowNode, FlowNodeCommons)


@register_type
class ReturnNode(graphene.ObjectType):
    class Meta:
        interfaces = (FlowNode, FlowNodeCommons)


@register_type
class ReactiveNode(graphene.ObjectType):
    implementation = graphene.Field(ReactiveImplementation, required=True)

    class Meta:
        interfaces = (FlowNode, FlowNodeCommons)


class FlowEdge(graphene.Interface):
    id = graphene.String(required=True)
    source = graphene.String(required=True)
    target = graphene.String(required=True)
    sourceHandle = graphene.String(required=True)
    targetHandle = graphene.String(required=True)
    typename = graphene.String(required=True)

    @classmethod
    def resolve_type(cls, instance, info):
        if instance["typename"] == "LabeledEdge":
            return LabeledEdge
        if instance["typename"] == "FancyEdge":
            return FancyEdge


class FlowEdgeCommons(graphene.Interface):
    stream = graphene.List(StreamItem, required=True)


@register_type
class LabeledEdge(graphene.ObjectType):
    stream = graphene.List(StreamItem, required=True)

    class Meta:
        interfaces = (FlowEdge, FlowEdgeCommons)


@register_type
class FancyEdge(graphene.ObjectType):
    stream = graphene.List(StreamItem, required=True)

    class Meta:
        interfaces = (FlowEdge, FlowEdgeCommons)


class ConstantKind(graphene.Enum):
    STRING = "STRING"
    INT = "INT"
    BOOL = "BOOL"
    FLOAT = "FLOAT"


class Global(graphene.ObjectType):
    to_keys = graphene.List(graphene.String, required=True)
    port = graphene.Field(Port, required=True)


class FlowGraph(graphene.ObjectType):
    zoom = graphene.Float()
    position = graphene.List(graphene.Int)
    nodes = graphene.List(FlowNode, required=True)
    edges = graphene.List(FlowEdge, required=True)
    globals = graphene.List(Global, required=True)
    args = graphene.List(Port, required=True)
    returns = graphene.List(Port, required=True)


class Flow(BalderObject, PinnableMixin):
    zoom = graphene.Float()
    position = graphene.List(graphene.Int)
    graph = graphene.Field(FlowGraph, required=True)
    name = graphene.String(required=True)

    def resolve_screenshot(root, info, *args, **kwargs):
        return root.screenshot.url if root.screenshot else None

    def resolve_name(root, info, *args, **kwargs):
        return root.name or "Untitled"

    class Meta:
        model = models.Flow


class Workspace(BalderObject, PinnableMixin):
    restrict = graphene.List(graphene.String, required=True)
    latest_flow = graphene.Field(lambda: Flow, description="The latest flow")

    def resolve_latest_flow(self, info):
        return self.flows.order_by("-created_at").first()

    class Meta:
        model = models.Workspace


class ReactiveTemplate(BalderObject):
    name = graphene.String(required=True)
    instream = graphene.List(graphene.List(Port, required=True), required=True)
    outstream = graphene.List(graphene.List(Port, required=True), required=True)
    constream = graphene.List(graphene.List(Port, required=True), required=True)
    implementation = graphene.Field(ReactiveImplementation, required=True)
    constants = graphene.List(Port, required=False)

    class Meta:
        model = models.ReactiveTemplate


class Run(BalderObject, PinnableMixin):
    latest_snapshot = graphene.Field(lambda: Snapshot)

    def resolve_latest_snapshot(root, info, *args, **kwargs):
        return root.snapshots.order_by("-created_at").first()

    class Meta:
        model = models.Run


class RunLog(BalderObject):
    node = graphene.String(required=True)

    class Meta:
        model = models.RunLog


class RunEvent(BalderObject):
    value = EventValue(required=False)
    handle = graphene.String(required=True)
    source = graphene.String(required=True)
    caused_by = graphene.List(graphene.Int, required=False)

    class Meta:
        model = models.RunEvent


class Snapshot(BalderObject):
    class Meta:
        model = models.Snapshot


class Condition(BalderObject, PinnableMixin):
    latest_snapshot = graphene.Field(lambda: ConditionSnapshot)

    def resolve_latest_snapshot(root, info, *args, **kwargs):
        return root.snapshots.order_by("-created_at").first()

    class Meta:
        model = models.Condition


class ConditionEvent(BalderObject):
    value = graphene.String(required=True)
    state = graphene.Field(ContractStatus, required=True)
    source = graphene.String(required=False)

    class Meta:
        model = models.ConditionEvent


class ConditionSnapshot(BalderObject):
    class Meta:
        model = models.ConditionSnapshot

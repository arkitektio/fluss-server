from balder.types import BalderObject
from flow import models
from django.contrib.auth import get_user_model
import graphene
from graphene.types.generic import GenericScalar
from balder.registry import register_type
from flow.inputs import StreamKind
from flow.scalars import EventValue


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
    typename = graphene.String(required=True)

    @classmethod
    def resolve_type(cls, instance, info):
        if instance["typename"] == "ArkitektNode":
            return ArkitektNode
        if instance["typename"] == "ReactiveNode":
            return ReactiveNode
        if instance["typename"] == "ArgNode":
            return ArgNode
        if instance["typename"] == "KwargNode":
            return KwargNode
        if instance["typename"] == "ReturnNode":
            return ReturnNode


class StreamItem(graphene.ObjectType):
    key = graphene.String(required=True)
    kind = StreamKind(required=True)
    identifier = graphene.String(required=False)


class FlowNodeCommons(graphene.Interface):
    instream = graphene.List(graphene.List(StreamItem, required=True), required=True)
    outstream = graphene.List(graphene.List(StreamItem, required=True), required=True)
    constream = graphene.List(graphene.List(StreamItem, required=True), required=True)
    constants = GenericScalar()


@register_type
class ArkitektNode(graphene.ObjectType):
    package = graphene.String()
    interface = graphene.String()
    name = graphene.String()
    description = graphene.String()
    kind = graphene.String(required=True)
    defaults = GenericScalar(required=False)

    class Meta:
        interfaces = (FlowNode, FlowNodeCommons)


class Widget(graphene.ObjectType):
    kind = graphene.String(required=True)
    query = graphene.String()


class Port(graphene.ObjectType):
    key = graphene.String(required=True)
    label = graphene.String()
    identifier = graphene.String()
    name = graphene.String()
    kind = StreamKind(required=True)
    description = graphene.String()
    widget = graphene.Field(Widget)


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
    implementation = graphene.String()

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


class Constant(graphene.ObjectType):
    key = graphene.String(required=True)
    value = graphene.String(required=True)


class Global(graphene.ObjectType):
    locked = graphene.Boolean(required=False)
    key = graphene.String(required=True)
    typename = graphene.String(required=True)
    identifier = graphene.String(required=False)
    value = GenericScalar(required=False)
    widget = GenericScalar(required=False)
    mapped = graphene.List(graphene.String, required=False)


class FlowGraph(graphene.ObjectType):
    zoom = graphene.Float()
    position = graphene.List(graphene.Int)
    nodes = graphene.List(FlowNode, required=True)
    edges = graphene.List(FlowEdge, required=True)
    globals = graphene.List(Global, required=True)
    args = graphene.List(Port, required=True)
    kwargs = graphene.List(Port, required=True)
    returns = graphene.List(Port, required=True)


class Flow(BalderObject):
    zoom = graphene.Float()
    position = graphene.List(graphene.Int)
    graph = graphene.Field(FlowGraph, required=True)
    name = graphene.String(required=True)

    def resolve_screenshot(root, info, *args, **kwargs):
        return root.screenshot.url if root.screenshot else None

    class Meta:
        model = models.Flow


class Diagram(BalderObject):
    latest_flow = graphene.Field(lambda: Flow, description="The latest flow")

    def resolve_latest_flow(self, info):
        return self.flows.order_by("-created_at").first()

    class Meta:
        model = models.Diagram


class Run(BalderObject):
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

    class Meta:
        model = models.RunEvent


class Snapshot(BalderObject):
    class Meta:
        model = models.Snapshot

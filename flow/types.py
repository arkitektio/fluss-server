from sys import implementation
from balder.types import BalderObject
from flow import models
from django.contrib.auth import get_user_model
import graphene
from graphene.types.generic import GenericScalar
from balder.registry import register_type


class Position(graphene.ObjectType):
    x = graphene.Int(required=True)
    y = graphene.Int(required=True)


class Graph(BalderObject):
    class Meta:
        model = models.Graph


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
    type = graphene.String()
    description = graphene.String()


class FlowKwarg(graphene.ObjectType):
    key = graphene.String(required=True)
    label = graphene.String()
    name = graphene.String()
    type = graphene.String()
    description = graphene.String()


class FlowReturn(graphene.ObjectType):
    key = graphene.String(required=True)

    label = graphene.String()
    name = graphene.String()
    type = graphene.String()
    description = graphene.String()


class FlowNode(graphene.Interface):
    id = graphene.String(required=True)
    position = graphene.Field(Position, required=True)

    @classmethod
    def resolve_type(cls, instance, info):
        if instance["type"] == "ArkitektNode":
            return ArkitektNode
        if instance["type"] == "ReactiveNode":
            return ReactiveNode
        if instance["type"] == "ArgNode":
            return ArgNode
        if instance["type"] == "KwargNode":
            return KwargNode
        if instance["type"] == "ReturnNode":
            return ReturnNode


class FlowNodeCommons(graphene.Interface):
    args = graphene.List(FlowArg)
    kwargs = graphene.List(FlowKwarg)
    returns = graphene.List(FlowReturn)


@register_type
class ArkitektNode(graphene.ObjectType):
    package = graphene.String()
    interface = graphene.String()
    name = graphene.String()
    description = graphene.String()
    kind = graphene.String(required=True)

    class Meta:
        interfaces = (FlowNode, FlowNodeCommons)


@register_type
class ArgNode(graphene.ObjectType):
    extra = graphene.String()

    class Meta:
        interfaces = (FlowNode, FlowNodeCommons)


@register_type
class KwargNode(graphene.ObjectType):
    extra = graphene.String()

    class Meta:
        interfaces = (FlowNode, FlowNodeCommons)


@register_type
class ReturnNode(graphene.ObjectType):
    extra = graphene.String()

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

    @classmethod
    def resolve_type(cls, instance, info):
        if instance["type"] == "LabeledEdge":
            return LabeledEdge
        if instance["type"] == "FancyEdge":
            return FancyEdge


class FlowEdgeCommons(graphene.Interface):
    label = graphene.String()


@register_type
class LabeledEdge(graphene.ObjectType):

    label = graphene.String()

    class Meta:
        interfaces = (FlowEdge, FlowEdgeCommons)


@register_type
class FancyEdge(graphene.ObjectType):

    label = graphene.String()

    class Meta:
        interfaces = (FlowEdge, FlowEdgeCommons)


class FlowGraph(graphene.ObjectType):
    zoom = graphene.Float()
    position = graphene.List(graphene.Int)
    nodes = graphene.List(FlowNode)
    edges = graphene.List(FlowEdge)


class Flow(BalderObject):
    zoom = graphene.Float()
    position = graphene.List(graphene.Int)
    nodes = graphene.List(FlowNode)
    edges = graphene.List(FlowEdge)

    class Meta:
        model = models.Flow

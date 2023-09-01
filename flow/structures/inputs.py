import graphene
from .scalars import Any, GenericScalar, SearchQuery, Identifier
from .enums import LogicalCondition, EffectKind
from .dynamic_enums import WidgetKind, ReturnWidgetKind, AnnotationKind


class PortKindInput(graphene.Enum):
    INT = "INT"
    STRING = "STRING"
    STRUCTURE = "STRUCTURE"
    LIST = "LIST"
    BOOL = "BOOL"
    DICT = "DICT"
    FLOAT = "FLOAT"
    UNION = "UNION"
    DATE = "DATE"


class ChoiceInput(graphene.InputObjectType):
    value = Any(required=True)
    label = graphene.String(required=True)
    description = graphene.String(required=False)


class Scope(graphene.Enum):
    GLOBAL = "GLOBAL"
    LOCAL = "LOCAL"


class NodeScope(graphene.Enum):
    GLOBAL = "GLOBAL"
    LOCAL = "LOCAL"
    BRIDGE_GLOBAL_TO_LOCAL = "BRIDGE_GLOBAL_TO_LOCAL"
    BRIDGE_LOCAL_TO_GLOBAL = "BRIDGE_LOCAL_TO_GLOBAL"


class TemplateFieldInput(graphene.InputObjectType):
    parent = graphene.String(required=False, description="The parent key (if nested)")
    key = graphene.String(required=True, description="The key of the field")
    type = graphene.String(required=True, description="The key of the field")
    description = graphene.String(
        required=False, description="A short description of the field"
    )


class DependencyInput(graphene.InputObjectType):
    key = graphene.String(
        required=False, description="The key of the port, defaults to self"
    )
    condition = graphene.Argument(
        LogicalCondition, required=True, description="The condition of the dependency"
    )
    value = GenericScalar(required=True)


class EffectInput(graphene.InputObjectType):
    dependencies = graphene.List(
        DependencyInput, description="The dependencies of this effect"
    )
    kind = graphene.Argument(
        EffectKind, required=True, description="The condition of the dependency"
    )
    message = graphene.String()


class WidgetInput(graphene.InputObjectType):
    kind = graphene.Argument(WidgetKind, description="type", required=True)
    query = SearchQuery(description="Do we have a possible")

    choices = graphene.List(ChoiceInput, description="The dependencies of this port")
    max = graphene.Int(description="Max value for int widget")
    min = graphene.Int(description="Max value for int widget")
    placeholder = graphene.String(description="Placeholder for any widget")
    as_paragraph = graphene.Boolean(description="Is this a paragraph")
    hook = graphene.String(description="A hook for the app to call")
    ward = graphene.String(description="A ward for the app to call")
    fields = graphene.List(
        TemplateFieldInput,
        description="The fields of this widget (onbly on TemplateWidget)",
        required=False,
    )


class ReturnWidgetInput(graphene.InputObjectType):
    kind = graphene.Argument(ReturnWidgetKind, description="type", required=True)
    choices = graphene.List(ChoiceInput, description="The dependencies of this port")
    query = graphene.String(description="Do we have a possible")
    hook = graphene.String(description="A hook for the app to call")
    ward = graphene.String(description="A hook for the app to call")


class ChildPortInput(graphene.InputObjectType):
    identifier = Identifier(description="The identifier")
    scope = graphene.Argument(
        Scope, description="The scope of this port", required=True
    )
    name = graphene.String(description="The name of this port")
    kind = PortKindInput(description="The type of this port")
    child = graphene.Field(lambda: ChildPortInput, description="The child port")
    nullable = graphene.Boolean(description="Is this argument nullable", required=True)
    annotations = graphene.List(
        lambda: AnnotationInput, description="The annotations of this argument"
    )
    variants = graphene.List(
        lambda: ChildPortInput,
        description="The varients of this port (only for union)",
        required=False,
    )
    assign_widget = graphene.Field(
        WidgetInput, description="The child of this argument"
    )
    return_widget = graphene.Field(
        ReturnWidgetInput, description="The child of this argument"
    )


class AnnotationInput(graphene.InputObjectType):
    kind = graphene.Argument(
        AnnotationKind, description="The kind of annotation", required=True
    )
    name = graphene.String(description="The name of this annotation")
    args = graphene.String(description="The value of this annotation")
    min = graphene.Float(description="The min of this annotation (Value Range)")
    max = graphene.Float(description="The max of this annotation (Value Range)")
    hook = graphene.String(description="A hook for the app to call")
    attribute = graphene.String(description="The attribute to check")
    annotations = graphene.List(
        lambda: AnnotationInput, description="The annotation of this annotation"
    )


class PortInput(graphene.InputObjectType):
    effects = graphene.List(EffectInput, description="The dependencies of this port")
    identifier = Identifier(description="The identifier")
    key = graphene.String(description="The key of the arg", required=True)
    scope = graphene.Argument(
        Scope, description="The scope of this port", required=True
    )
    variants = graphene.List(
        ChildPortInput,
        description="The varients of this port (only for union)",
        required=False,
    )
    name = graphene.String(description="The name of this argument")
    label = graphene.String(description="The name of this argument")
    kind = PortKindInput(description="The type of this argument", required=True)
    description = graphene.String(description="The description of this argument")
    child = graphene.Field(ChildPortInput, description="The child of this argument")
    assign_widget = graphene.Field(
        WidgetInput, description="The child of this argument"
    )
    return_widget = graphene.Field(
        ReturnWidgetInput, description="The child of this argument"
    )
    default = Any(description="The key of the arg", required=False)
    nullable = graphene.Boolean(description="Is this argument nullable", required=True)
    annotations = graphene.List(
        AnnotationInput, description="The annotations of this argument"
    )
    groups = graphene.List(
        graphene.String, description="The port group of this argument"
    )

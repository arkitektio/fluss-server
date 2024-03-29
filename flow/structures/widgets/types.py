from balder.registry import register_type
import graphene
from graphene.types.generic import GenericScalar
from ..types import Choice


widget_types = {
    "QueryWidget": lambda: QueryWidget,
    "IntWidget": lambda: IntWidget,
    "StringWidget": lambda: StringWidget,
    "SearchWidget": lambda: SearchWidget,
    "SliderWidget": lambda: SliderWidget,
    "LinkWidget": lambda: LinkWidget,
    "BoolWidget": lambda: BoolWidget,
    "ChoiceWidget": lambda: ChoiceWidget,
    "CustomWidget": lambda: CustomWidget,
    "TemplateWidget": lambda: TemplateWidget,
    "DateWidget": lambda: DateWidget,
    "ColorWidget": lambda: ColorWidget,
}


@register_type
class Widget(graphene.Interface):
    kind = graphene.String(required=True)

    @classmethod
    def resolve_type(cls, instance, info):
        typemap = widget_types
        _type = instance.get("kind")
        return typemap.get(_type, lambda: Widget)()


@register_type
class QueryWidget(graphene.ObjectType):
    query = graphene.String(description="A Complex description")

    class Meta:
        interfaces = (Widget,)


@register_type
class LinkWidget(graphene.ObjectType):
    linkbuilder = graphene.String(description="A Complex description")

    class Meta:
        interfaces = (Widget,)


@register_type
class SearchWidget(graphene.ObjectType):
    query = graphene.String(description="A Complex description", required=True)
    ward = graphene.String(description="A ward for the app to call", required=True)

    class Meta:
        interfaces = (Widget,)


@register_type
class BoolWidget(graphene.ObjectType):
    class Meta:
        interfaces = (Widget,)


@register_type
class ChoiceWidget(graphene.ObjectType):
    choices = graphene.List(Choice, description="A list of choices")

    class Meta:
        interfaces = (Widget,)


@register_type
class IntWidget(graphene.ObjectType):
    query = graphene.String(description="A Complex description")

    class Meta:
        interfaces = (Widget,)


@register_type
class SliderWidget(graphene.ObjectType):
    min = graphene.Float(description="A Complex description")
    max = graphene.Float(description="A Complex description")
    step = graphene.Float(description="A Complex description")

    class Meta:
        interfaces = (Widget,)


@register_type
class StringWidget(graphene.ObjectType):
    placeholder = graphene.String(description="A placeholder to display")
    as_paragraph = graphene.Boolean(description="Whether to display as paragraph")

    class Meta:
        interfaces = (Widget,)


@register_type
class CustomWidget(graphene.ObjectType):
    hook = graphene.String(description="A hook for the ward to call")
    ward = graphene.String(description="A ward for the app to call")

    class Meta:
        interfaces = (Widget,)


@register_type
class DateWidget(graphene.ObjectType):
    start_date = graphene.String(description="A start date")

    class Meta:
        interfaces = (Widget,)


@register_type
class ColorWidget(graphene.ObjectType):
    start_date = graphene.String(description="A start date")

    class Meta:
        interfaces = (Widget,)


class TemplateField(graphene.ObjectType):
    parent = graphene.String(required=False, description="The parent key (if nested)")
    key = graphene.String(required=True, description="The key of the field")
    type = graphene.String(required=True, description="The type of the field")
    description = graphene.String(
        required=True, description="A short description of the field"
    )


@register_type
class TemplateWidget(graphene.ObjectType):
    fields = graphene.List(TemplateField, required=True)

    class Meta:
        interfaces = (Widget,)

from .annotations import annotation_types
from .widgets.types import widget_types
from .widgets.returns import return_widget_types
import graphene


AnnotationKind = type(
    "AnnotationKind",
    (graphene.Enum,),
    {
        "__doc__": "The kind of annotation",
        **{key: key for key, value in annotation_types.items()},
    },
)
WidgetKind = type(
    "WidgetKind",
    (graphene.Enum,),
    {
        "__doc__": "The kind of widget",
        **{key: key for key, value in widget_types.items()},
    },
)
ReturnWidgetKind = type(
    "ReturnWidgetKind",
    (graphene.Enum,),
    {
        "__doc__": "The kind of return widget",
        **{key: key for key, value in return_widget_types.items()},
    },
)

import strawberry
from kante.types import Info

from reaktion import models, types


def reactive_template(info: Info, id: strawberry.ID) -> types.ReactiveTemplate:
    return models.ReactiveTemplate.objects.get(id=id)

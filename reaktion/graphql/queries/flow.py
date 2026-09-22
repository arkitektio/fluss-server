import strawberry
from kante.types import Info
from reaktion import models, types


def flow(info: Info, id: strawberry.ID) -> types.Flow:
    return models.Flow.objects.get(id=id)

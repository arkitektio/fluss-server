import strawberry
from kante.types import Info

from reaktion import models, types
from reaktion.scoping import get_for_org


def workspace(info: Info, id: strawberry.ID) -> types.Workspace:
    return get_for_org(models.Workspace, info, id=id)

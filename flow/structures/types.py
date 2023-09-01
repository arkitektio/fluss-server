import graphene
from graphene.types.generic import GenericScalar


class Choice(graphene.ObjectType):
    value = GenericScalar(required=True)
    label = graphene.String(required=True)
    description = graphene.String(required=False)

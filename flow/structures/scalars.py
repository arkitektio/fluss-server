from graphene.types import Scalar
from graphene.types.generic import GenericScalar
from graphql.language import ast
import graphene


class Any(GenericScalar):
    """Any any field"""


class AnyInput(GenericScalar):
    """Any any field"""


class SearchQuery(graphene.String):
    """Search query"""


class Identifier(graphene.String):
    """A unique Structure identifier"""

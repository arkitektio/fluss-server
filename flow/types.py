from balder.types import BalderObject
from flow import models
from django.contrib.auth import get_user_model
import graphene


class Graph(BalderObject):
    class Meta:
        model = models.Graph


class User(BalderObject):
    class Meta:
        model = get_user_model()


class Deployed(graphene.ObjectType):
    status = graphene.String(default_value="Ok")

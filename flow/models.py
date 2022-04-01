from re import template
from django.db import models
from django.contrib.auth import get_user_model
import namegenerator

# Create your models here.


class Graph(models.Model):
    """Graph is a Template for a Template"""

    template = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="The associated Template on Arkitekt",
    )
    creator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True
    )
    version = models.CharField(max_length=100, default="1.0alpha")
    name = models.CharField(max_length=100, null=True, default=namegenerator.gen)
    diagram = models.JSONField(null=True, blank=True)
    description = models.CharField(
        max_length=50000, default="Add a Description", blank=True, null=True
    )

    def __str__(self):
        return f"{self.name}"


class Flow(models.Model):

    creator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True
    )
    version = models.CharField(max_length=100, default="1.0alpha")
    name = models.CharField(max_length=100, null=True, default=namegenerator.gen)
    nodes = models.JSONField(null=True, blank=True, default=list)
    edges = models.JSONField(null=True, blank=True, default=list)
    description = models.CharField(
        max_length=50000, default="Add a Description", blank=True, null=True
    )

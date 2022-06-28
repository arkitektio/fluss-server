from re import template
from django.db import models
from django.contrib.auth import get_user_model
from pyparsing import null_debug_action
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
    graph = models.JSONField(null=True, blank=True)
    description = models.CharField(
        max_length=50000, default="Add a Description", blank=True, null=True
    )
    brittle = models.BooleanField(
        default=False,
        help_text="Is this a brittle flow? aka. should the flow fail on any exception?",
    )


class Run(models.Model):

    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, null=True, blank=True)
    assignation = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.flow.name} - {self.assignation}"


class Snapshot(models.Model):

    run = models.ForeignKey(Run, on_delete=models.CASCADE, null=True, blank=True)
    assignation = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)


class RunLog(models.Model):

    run = models.ForeignKey(Run, on_delete=models.CASCADE, null=True, blank=True)
    log = models.CharField(max_length=100, null=True, blank=True)
    node = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.run}"

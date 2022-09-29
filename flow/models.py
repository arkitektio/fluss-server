from datetime import datetime
from django.db import models
from django.contrib.auth import get_user_model
import namegenerator
from flow.enums import EventType, ReactiveImplementation, ReactiveImplementationModel
from flow.storage import PrivateMediaStorage
import uuid

# Create your models here.


class Diagram(models.Model):
    """Graph is a Template for a Template"""

    name = models.CharField(max_length=100, null=True, default=namegenerator.gen)
    creator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.name}"


class Flow(models.Model):
    diagram = models.ForeignKey(
        Diagram, on_delete=models.CASCADE, null=True, blank=True, related_name="flows"
    )
    creator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True
    )
    version = models.CharField(max_length=100, default="1.0alpha")
    name = models.CharField(max_length=100, null=True, default=namegenerator.gen)
    nodes = models.JSONField(null=True, blank=True, default=list)
    edges = models.JSONField(null=True, blank=True, default=list)
    graph = models.JSONField(null=True, blank=True)
    hash = models.CharField(max_length=4000, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    screenshot = models.ImageField(null=True, storage=PrivateMediaStorage())
    description = models.CharField(
        max_length=50000, default="Add a Dessscription", blank=True, null=True
    )
    brittle = models.BooleanField(
        default=False,
        help_text="Is this a brittle flow? aka. should the flow fail on any exception?",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["diagram", "hash"],
                name="Equal Reservation on this App by this Waiter is already in place",
            )
        ]


class Run(models.Model):

    flow = models.ForeignKey(
        Flow, on_delete=models.CASCADE, null=True, blank=True, related_name="runs"
    )
    assignation = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.flow.name} - {self.assignation}"


class Snapshot(models.Model):

    run = models.ForeignKey(
        Run, on_delete=models.CASCADE, null=True, blank=True, related_name="snapshots"
    )
    t = models.IntegerField()
    status = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)


class RunLog(models.Model):

    run = models.ForeignKey(
        Run, on_delete=models.CASCADE, null=True, blank=True, related_name="logs"
    )
    log = models.CharField(max_length=100, null=True, blank=True)
    node = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.run}"


class RunEvent(models.Model):

    run = models.ForeignKey(
        Run, on_delete=models.CASCADE, null=True, blank=True, related_name="events"
    )
    snapshot = models.ManyToManyField(Snapshot, related_name="events")
    type = models.CharField(
        max_length=1000,
        choices=EventType.choices,
        default=EventType.UNKNOWN.value,
    )
    t = models.IntegerField()
    source = models.CharField(max_length=1000)
    handle = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)
    value = models.JSONField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Events for {self.run}"


class ReactiveTemplate(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=1000, null=True, blank=True)
    implementation = models.CharField(
        max_length=1000,
        choices=ReactiveImplementationModel.choices,
        default=ReactiveImplementationModel.ZIP.value,
    )
    instream = models.JSONField(null=True, blank=True, default=list)
    outstream = models.JSONField(null=True, blank=True, default=list)
    constream = models.JSONField(null=True, blank=True, default=list)
    defaults = models.JSONField(null=True, blank=True)


import flow.signals

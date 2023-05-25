from datetime import datetime
from django.db import models
from django.contrib.auth import get_user_model
import namegenerator
from flow.enums import EventType, ReactiveImplementation, ReactiveImplementationModel
from flow.storage import PrivateMediaStorage
import uuid
from lok.models import LokClient
# Create your models here.


class CreatedThroughMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_created_by")
    created_through = models.ForeignKey(
        LokClient, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_created_through"
    )
    created_while = models.CharField(max_length=1000, null=True, blank=True)

    class Meta:
        abstract = True

class Workspace(CreatedThroughMixin,  models.Model):
    """Graph is a Template for a Template"""

    restrict = models.JSONField(
        default=list, help_text="Restrict access to specific nodes for this diagram"
    )
    name = models.CharField(max_length=100, null=True, default=namegenerator.gen)
    creator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True
    )
    pinned_by = models.ManyToManyField(
        get_user_model(),
        related_name="pinned_workspaces",
        blank=True,
        help_text="The users that have pinned the position",
    )

    def __str__(self):
        return f"{self.name}"


class Flow(CreatedThroughMixin, models.Model):
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name="flows"
    )
    creator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True
    )
    restrict = models.JSONField(
        default=list, help_text="Restrict access to specific nodes for this diagram"
    )
    version = models.CharField(max_length=100, default="1.0alpha")
    name = models.CharField(max_length=100, null=True, default=namegenerator.gen)
    nodes = models.JSONField(null=True, blank=True, default=list)
    edges = models.JSONField(null=True, blank=True, default=list)
    graph = models.JSONField(null=True, blank=True)
    hash = models.CharField(max_length=4000, default=uuid.uuid4)
    screenshot = models.ImageField(null=True, storage=PrivateMediaStorage())
    description = models.CharField(
        max_length=50000, default="Add a Desssscription", blank=True, null=True
    )
    brittle = models.BooleanField(
        default=False,
        help_text="Is this a brittle flow? aka. should the flow fail on any exception?",
    )
    pinned_by = models.ManyToManyField(
        get_user_model(),
        related_name="pinned_flows",
        blank=True,
        help_text="The users that have pinned the position",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "hash"],
                name="Equal Reservation on this App by this Waiter is already in place",
            )
        ]


class Run(CreatedThroughMixin, models.Model):
    flow = models.ForeignKey(
        Flow, on_delete=models.CASCADE, null=True, blank=True, related_name="runs"
    )
    assignation = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    snapshot_interval = models.IntegerField(null=True, blank=True)
    pinned_by = models.ManyToManyField(
        get_user_model(),
        related_name="pinned_runs",
        blank=True,
        help_text="The users that have pinned the position",
    )

    def __str__(self) -> str:
        return f"{self.flow.workspace.name} - {self.assignation}"




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
    caused_by = models.JSONField(default=list, blank=True)
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
        unique=True,
    )
    instream = models.JSONField(null=True, blank=True, default=list)
    outstream = models.JSONField(null=True, blank=True, default=list)
    constream = models.JSONField(null=True, blank=True, default=list)
    defaults = models.JSONField(null=True, blank=True)
    constants = models.JSONField(null=True, blank=True, default=list)

class Condition(CreatedThroughMixin, models.Model):
    flow = models.ForeignKey(
        Flow, on_delete=models.CASCADE, null=True, blank=True, related_name="conditions"
    )
    provision = models.CharField(max_length=100, null=True, blank=True)
    snapshot_interval = models.IntegerField(null=True, blank=True)
    pinned_by = models.ManyToManyField(
        get_user_model(),
        related_name="pinned_conditions",
        blank=True,
        help_text="The users that have pinned the position",
    )

    def __str__(self) -> str:
        return f"{self.flow.name} - {self.provision}"
    
class ConditionSnapshot(models.Model):
    condition = models.ForeignKey(
        Condition, on_delete=models.CASCADE, null=True, blank=True, related_name="snapshots"
    )
    status = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)

class ConditionEvent(models.Model):
    condition = models.ForeignKey(
        Condition, on_delete=models.CASCADE, null=True, blank=True, related_name="events"
    )
    snapshot = models.ManyToManyField(ConditionSnapshot, related_name="events")
    source = models.CharField(max_length=1000)
    value = models.CharField(max_length=1000, blank=True)
    state = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)


import flow.signals

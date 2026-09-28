import uuid

from django.contrib.auth import get_user_model
from authentikate.models import Organization, User

# Create your models here.
from django.db import models

# Create your models here.
from django_choices_field import TextChoicesField
from embeddings.models import EmbeddedDescriptionMixin, embedding_indexes

from . import enums


class Workspace(EmbeddedDescriptionMixin, models.Model):
    """Graph is a Template for a Template

    Carries an embedding of its title + description (``EmbeddedDescriptionMixin``) so the
    workspace list's ``search`` finds it by what it is about, not only by a substring.
    """

    embedding_source_fields = ("title", "description")

    restrict = models.JSONField(
        default=list,
        help_text="Restrict access to specific nodes for this diagram okay?",
    )
    title = models.CharField(max_length=10000, null=True)
    description = models.CharField(max_length=10000, null=True)
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)
    pinned_by = models.ManyToManyField(
        get_user_model(),
        related_name="pinned_workspaces",
        blank=True,
        help_text="The users that have pinned the workspace",
    )

    def __str__(self):
        return f"{self.title}"

    class Meta:
        # The embedding healer's "any row not by the current model?" probe.
        indexes = [*embedding_indexes("workspace")]


class Flow(EmbeddedDescriptionMixin, models.Model):
    """One saved version of a workspace's graph; embeds its title + description for ``search``."""

    embedding_source_fields = ("title", "description")

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name="flows")
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    restrict = models.JSONField(default=list, help_text="Restrict access to specific nodes for this diagram")
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
    )
    version = models.CharField(max_length=100, default="1.0alpha")
    title = models.CharField(max_length=10000, null=True)
    description = models.CharField(max_length=10000, null=True)
    nodes = models.JSONField(null=True, blank=True, default=list)
    edges = models.JSONField(null=True, blank=True, default=list)
    graph = models.JSONField(null=True, blank=True)
    hash = models.CharField(max_length=4000, default=uuid.uuid4)
    description = models.CharField(max_length=50000, default="Add a Desssscription", blank=True, null=True)
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
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "hash"],
                name="Equal Reservation on this App by this Waiter is already in place",
            )
        ]
        # The embedding healer's "any row not by the current model?" probe.
        indexes = [*embedding_indexes("flow")]


class ReactiveTemplate(models.Model):
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=1000, null=True, blank=True)
    implementation = TextChoicesField(
        max_length=1000,
        choices_enum=enums.ReactiveImplementationChoices,
        default=enums.ReactiveImplementationChoices.ZIP.value,
        help_text="Check async Programming Textbook",
    )
    ins = models.JSONField(null=True, blank=True, default=list)
    outs = models.JSONField(null=True, blank=True, default=list)
    voids = models.JSONField(null=True, blank=True, default=list)
    constants = models.JSONField(null=True, blank=True, default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["title", "description"],
                name="Only one Reactive Template with this title and description",
            )
        ]


# Montoring Classes
class Run(models.Model):
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, null=True, blank=True, related_name="runs")

    task_id = models.CharField(null=True, blank=True, max_length=1000)
    status = models.CharField(max_length=100, default="RUNNING")
    snapshot_interval = models.IntegerField(null=True, blank=True)
    pinned_by = models.ManyToManyField(
        get_user_model(),
        related_name="pinned_runs",
        blank=True,
        help_text="The users that have pinned the position",
    )
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.flow.workspace} - {self.task_id}"


class Snapshot(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, null=True, blank=True, related_name="snapshots")
    t = models.IntegerField()
    status = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)


class RunEvent(models.Model):
    reference = models.CharField(max_length=1000, null=True, blank=True)
    run = models.ForeignKey(Run, on_delete=models.CASCADE, null=True, blank=True, related_name="events")
    snapshot = models.ManyToManyField(Snapshot, related_name="events")
    kind = TextChoicesField(
        max_length=1000,
        choices_enum=enums.RunEventKindChoices,
        default=enums.RunEventKindChoices.NEXT.value,
        help_text="The type of event",
    )
    t = models.IntegerField()
    caused_by = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=1000)
    handle = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)
    value = models.JSONField(null=True, blank=True)
    exception = models.CharField(max_length=2000, blank=True, null=True)

    def __str__(self) -> str:
        return f"Events for {self.run}"



class PythonFlow(EmbeddedDescriptionMixin, models.Model):
    """One immutable version of a flow written as Python source (not a graph).

    Versions of the same flow share a ``lineage`` (minted on the first, copied from ``previous``
    on each next one); identical content within a lineage is the same row. ``args``, ``returns``
    and ``manifest`` are what the executor's validation derived from the source -- the manifest
    lists every action the code may call and is its permission boundary. Only PUBLISHED versions
    are registered as actions.
    """

    embedding_source_fields = ("title", "description")

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    creator = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name="python_flows")
    title = models.CharField(max_length=10000, null=True)
    description = models.CharField(max_length=50000, null=True, blank=True)
    lineage = models.UUIDField(default=uuid.uuid4, help_text="Shared by every version of the same flow")
    previous = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="next_versions")
    source = models.TextField()
    entrypoint = models.CharField(max_length=1000, default="main")
    args = models.JSONField(default=list, help_text="The ArgPorts derived from the entrypoint's signature")
    returns = models.JSONField(default=list, help_text="The ReturnPorts derived from the entrypoint's signature")
    manifest = models.JSONField(default=list, help_text="Every action the source may call, under the name it is injected as")
    runtime = models.CharField(max_length=1000, help_text="The executor runtime (interpreter + helpers) the source was validated against")
    status = TextChoicesField(max_length=100, choices_enum=enums.PythonFlowStatusChoices, default=enums.PythonFlowStatusChoices.DRAFT.value)
    hash = models.CharField(max_length=64, help_text="sha256 over source, entrypoint, manifest and runtime")
    pinned_by = models.ManyToManyField(get_user_model(), related_name="pinned_python_flows", blank=True)
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "lineage", "hash"], name="pyflow_unique_version")]
        indexes = [*embedding_indexes("pyflow")]

    def __str__(self) -> str:
        return f"{self.title} ({self.hash[:8]})"

    @property
    def is_physical(self) -> bool:
        """Whether the source may call an action that touches the real world."""
        return any(entry.get("effect") == "PHYSICAL" for entry in self.manifest or [])


class PythonRun(models.Model):
    """One execution of a published PythonFlow; its step-by-step history is the rekuest task tree."""

    # Only drafts can be deleted (see ``delete_python_flow``) and drafts never run, so a flow
    # with runs goes only with its organization -- and then its runs go with it.
    flow = models.ForeignKey(PythonFlow, on_delete=models.CASCADE, related_name="runs")
    task_id = models.CharField(max_length=1000)
    status = TextChoicesField(max_length=100, choices_enum=enums.PythonRunStatusChoices, default=enums.PythonRunStatusChoices.RUNNING.value)
    pinned_by = models.ManyToManyField(get_user_model(), related_name="pinned_python_runs", blank=True)
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["flow", "task_id"], name="pyrun_unique_task")]


class Trace(models.Model):
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, null=True, blank=True, related_name="traces")
    provision = models.JSONField(null=True, blank=True, max_length=1000)
    snapshot_interval = models.IntegerField(null=True, blank=True)
    pinned_by = models.ManyToManyField(
        get_user_model(),
        related_name="pinned_conditions",
        blank=True,
        help_text="The users that have pinned the position",
    )

    def __str__(self) -> str:
        return f"{self.flow.name} - {self.provision}"


class TraceSnapshot(models.Model):
    trace = models.ForeignKey(Trace, on_delete=models.CASCADE, null=True, blank=True, related_name="snapshots")
    status = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)


class TraceEvent(models.Model):
    trace = models.ForeignKey(Trace, on_delete=models.CASCADE, null=True, blank=True, related_name="events")
    snapshot = models.ManyToManyField(TraceSnapshot, related_name="events")
    source = models.CharField(max_length=1000)
    value = models.CharField(max_length=1000, blank=True)
    state = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)


from .signals import *

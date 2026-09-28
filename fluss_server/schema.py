import strawberry
from fluss_server.logs import QuietErrorsSchema
import kante
from strawberry_django.optimizer import DjangoOptimizerExtension
from reaktion import types, models
from reaktion.graphql import mutations
from reaktion.graphql import subscriptions
from reaktion.graphql import queries
from koherent.strawberry.extension import KoherentExtension
from authentikate.strawberry.extension import AuthentikateExtension
from strawberry.schema.config import StrawberryConfig
from kante.types import Info
from typing import List
from rekuest_core.constants import interface_types, input_union_types
from kante.unions import unionElementOf
from rekuest_core.scalars import scalar_map as rekuest_scalar_map
from reaktion.scalars import scalar_map as reaktion_scalar_map
from reaktion.scoping import get_for_org


@strawberry.type
class Query:
    """The root query type. All list fields are scoped to the requesting user's organization."""

    flows: list[types.Flow] = kante.django_field(description="List all flows in your organization.")
    runs: list[types.Run] = kante.django_field(description="List all runs in your organization.")
    snapshots: list[types.Snapshot] = kante.django_field(description="List all run snapshots in your organization.")
    workspaces: list[types.Workspace] = kante.django_field(description="List all workspaces in your organization.")
    workspace = kante.django_field(resolver=queries.workspace, description="Fetch a single workspace by id.")
    reactive_templates: list[types.ReactiveTemplate] = kante.django_field(description="List all reactive operator templates (a shared, global catalog).")
    reactive_template = kante.django_field(resolver=queries.reactive_template, description="Fetch a single reactive template by id.")
    events_between = kante.django_field(resolver=queries.events_between, description="Fetch the events of a run between two logical times, seeded from the latest snapshot at or before the lower bound.")

    python_flows: list[types.PythonFlow] = kante.django_field(description="List all Python flow versions in your organization.")
    python_runs: list[types.PythonRun] = kante.django_field(description="List all Python flow runs in your organization.")

    # Stats
    workspace_stats: types.WorkspaceStats = strawberry.field(resolver=types.WorkspaceStatsResolver, description="Aggregate statistics over the workspaces in your organization.")

    @kante.django_field(description="Fetch a single run by id.")
    def run(self, info: Info, id: strawberry.ID) -> types.Run:
        return models.Run.objects.get(id=id, flow__organization=info.context.request.organization)

    @kante.django_field(description="Fetch the run created for a given task id.")
    def run_for_task(self, info: Info, id: strawberry.ID) -> types.Run:
        return models.Run.objects.get(task_id=id, flow__organization=info.context.request.organization)

    @kante.django_field(description="Fetch a single flow by id.")
    def flow(self, info: Info, id: strawberry.ID) -> types.Flow:
        return get_for_org(models.Flow, info, id=id)

    @kante.django_field(description="Fetch a single Python flow version by id.")
    def python_flow(self, info: Info, id: strawberry.ID) -> types.PythonFlow:
        return get_for_org(models.PythonFlow, info, id=id)

    @kante.django_field(description="Fetch a single Python flow run by id.")
    def python_run(self, info: Info, id: strawberry.ID) -> types.PythonRun:
        return get_for_org(models.PythonRun, info, id=id)

    @kante.django_field(description="Fetch a single run snapshot by id.")
    def snapshot(self, info: Info, id: strawberry.ID) -> types.Snapshot:
        return models.Snapshot.objects.get(id=id, run__flow__organization=info.context.request.organization)


@strawberry.type
class Mutation:
    """The root mutation type. All mutations are scoped to the requesting user's organization."""

    update_workspace = kante.django_mutation(
        resolver=mutations.update_workspace,
        description="Update a workspace's metadata and upsert the flow for the posted graph.",
    )
    create_workspace = kante.django_mutation(
        resolver=mutations.create_workspace,
        description="Create a new workspace, seeded with an initial flow.",
    )
    create_run = kante.django_mutation(
        resolver=mutations.create_run,
        description="Start (or reuse) a run of a flow for a given task.",
    )
    close_run = kante.django_mutation(
        resolver=mutations.close_run,
        description="Mark a run as COMPLETED.",
    )
    delete_run = kante.django_mutation(
        resolver=mutations.delete_run,
        description="Delete a run and its events and snapshots.",
    )
    snapshot = kante.django_mutation(
        resolver=mutations.snapshot,
        description="Capture a state snapshot of a run at a logical time.",
    )
    delete_snapshot = kante.django_mutation(
        resolver=mutations.delete_snapshot,
        description="Delete a run snapshot.",
    )
    track = kante.django_mutation(
        resolver=mutations.track,
        description="Record a single run event (a value, error or completion) for a run.",
    )
    create_python_flow = kante.django_mutation(
        resolver=mutations.create_python_flow,
        description="Store a new DRAFT Python flow version (or return the existing one with the same content in its lineage).",
    )
    update_python_flow = kante.django_mutation(
        resolver=mutations.update_python_flow,
        description="Change a Python flow version's title or description.",
    )
    publish_python_flow = kante.django_mutation(
        resolver=mutations.publish_python_flow,
        description="Publish a DRAFT (or re-publish an ARCHIVED) Python flow version, so it is registered as an action.",
    )
    archive_python_flow = kante.django_mutation(
        resolver=mutations.archive_python_flow,
        description="Archive a PUBLISHED Python flow version, so it is no longer registered.",
    )
    delete_python_flow = kante.django_mutation(
        resolver=mutations.delete_python_flow,
        description="Delete a DRAFT Python flow version.",
    )
    create_python_run = kante.django_mutation(
        resolver=mutations.create_python_run,
        description="Start (or reuse) the run of a published Python flow version for a task.",
    )
    close_python_run = kante.django_mutation(
        resolver=mutations.close_python_run,
        description="Finish a Python flow run as COMPLETED or FAILED.",
    )


@strawberry.type
class Subscription:
    """The root subscription type."""

    events = strawberry.subscription(
        resolver=subscriptions.events,
        description="Subscribe to the live stream of events for a given run.",
    )


class Schema(QuietErrorsSchema, kante.Schema):
    """kante.Schema, logging expected resolver errors as one line and bugs with a traceback (see logs.py)."""


schema = Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[DjangoOptimizerExtension, KoherentExtension, AuthentikateExtension],
    config=StrawberryConfig(scalar_map={**rekuest_scalar_map, **reaktion_scalar_map}),
    types=[
        types.RekuestFilterActionNode,
        types.RekuestMapActionNode,
        types.RetriableNode,
        types.ArgNode,
        types.ReturnNode,
        types.VanillaEdge,
        types.LoggingEdge,
        types.ReactiveNode,
        types.AgentSubFlowNode,
    ]
    + interface_types
    + input_union_types,
    schema_directives=[unionElementOf],
)

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
from authentikate.strawberry import AuthExtension
from arkitekt_service.collaborations import graphql as collaboration_types
from arkitekt_service.collaborations.guests import object_scope
from arkitekt_service.graphql import CollaborationGate, annotate_schema
from django.db.models import Model
from fluss_server.service import service as fluss_service


def _fetch(model: type[Model], id: strawberry.ID, info: Info) -> Model:
    """An object of the request's organization by id: a run is its flow's (it has no organization path of its own)."""
    if model is models.Run:
        run: models.Run = models.Run.objects.get(id=id, flow__organization=info.context.request.organization)
        return run
    return get_for_org(model, info, id=id)


#: The collaborations of fluss's objects, which a guest of the organization is granted.
collaboration_api = collaboration_types.resolvers(fetch=_fetch)


#: Who makes and changes collaborations: full members who are admins or editors (a guest is refused every mutation).
COLLABORATING_ROLES = ["admin", "editor"]


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
    validate_python_flow = kante.django_field(
        resolver=queries.validate_python_flow,
        description="Check a Python flow's source against the actions it may call, as createPythonFlow would, without storing it: its ports, stubs and runtime, or why it would be refused.",
    )

    # Stats
    workspace_stats: types.WorkspaceStats = strawberry.field(resolver=types.WorkspaceStatsResolver, description="Aggregate statistics over the workspaces in your organization.")

    collaborations: list[collaboration_types.Collaboration] = kante.django_field(resolver=collaboration_api.collaborations, description="List the organization's collaborations: what a guest granted one sees of it (a guest: the collaborations granted to them)")
    collaboration: collaboration_types.Collaboration = kante.django_field(resolver=collaboration_api.collaboration, description="Get a single collaboration by ID")

    @kante.django_field(description="Fetch a single run by id.")
    def run(self, info: Info, id: strawberry.ID) -> types.Run:
        return object_scope(models.Run.objects.filter(flow__organization=info.context.request.organization), info=info).get(id=id)

    @kante.django_field(description="Fetch the run created for a given task id.")
    def run_for_task(self, info: Info, id: strawberry.ID) -> types.Run:
        return object_scope(models.Run.objects.filter(flow__organization=info.context.request.organization), info=info).get(task_id=id)

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
        return object_scope(models.Snapshot.objects.filter(run__flow__organization=info.context.request.organization), info=info).get(id=id)


@strawberry.type
class Mutation:
    """The root mutation type. All mutations are scoped to the requesting user's organization.

    None is open to a guest of the organization (none opts in with ``allow_scoped``): running a flow
    as a guest would act with the organization's agents."""

    create_collaboration = kante.django_mutation(extensions=[AuthExtension(any_role_of=COLLABORATING_ROLES)], resolver=collaboration_api.create_collaboration, description="Create an empty collaboration, to put objects in and grant a guest")
    add_to_collaboration = kante.django_mutation(extensions=[AuthExtension(any_role_of=COLLABORATING_ROLES)], resolver=collaboration_api.add_to_collaboration, description="Put an object in a collaboration, with what it needs to be seen: a run brings its flow, a flow its workspace, a workspace its flows")
    remove_from_collaboration = kante.django_mutation(extensions=[AuthExtension(any_role_of=COLLABORATING_ROLES)], resolver=collaboration_api.remove_from_collaboration, description="Take an object out of a collaboration, with what it brought that nothing else there needs")
    delete_collaboration = kante.django_mutation(extensions=[AuthExtension(any_role_of=COLLABORATING_ROLES)], resolver=collaboration_api.delete_collaboration, description="Delete a collaboration: whoever was granted it sees nothing of it any more")

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
        description="Validate a Python flow's source against the actions it may call and store it as a new DRAFT version, with the ports and runtime the validation derives (or return the existing one with the same content in its lineage). A source that does not validate is refused.",
    )
    update_python_flow = kante.django_mutation(
        resolver=mutations.update_python_flow,
        description="Change a Python flow version's title or description.",
    )
    publish_python_flow = kante.django_mutation(
        resolver=mutations.publish_python_flow,
        description="Publish a DRAFT (or re-publish an ARCHIVED) Python flow version, so it can run and be deployed as an action.",
    )
    archive_python_flow = kante.django_mutation(
        resolver=mutations.archive_python_flow,
        description="Archive a PUBLISHED Python flow version, so it no longer runs (its runs keep pointing at it).",
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
    # A guest of the organization is handed only what is in their collaborations (CollaborationGate, after
    # authentikate's extension, which reads the token).
    extensions=[DjangoOptimizerExtension, KoherentExtension, AuthentikateExtension, CollaborationGate],
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

# Which structure each type is (`@identified`), and, behind the gate, that fluss lets guests in.
annotate_schema(schema, fluss_service)

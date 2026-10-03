from dataclasses import Field
import kante
from reaktion import models, scalars, enums, filters, order
import strawberry
from typing import Optional
from pydantic import BaseModel, Field
from strawberry.experimental import pydantic
from typing import Any, Dict
from typing import Literal, Union
import datetime
from rekuest_core.objects import types as rtypes
from rekuest_core.objects import models as rmodels
from rekuest_core import enums as renums
from strawberry import LazyType
from strawberry.scalars import JSON
from kante.types import Info
from .type_gen import create_stats_type


def build_prescoped_queryset(info, queryset, field="organization"):
    if info.variable_values.get("filters", {}).get("scope") is None:
        queryset = queryset.filter(**{field: info.context.request.organization})
        return queryset

    else:
        raise Exception("Custom scopes not implemented yet")


def build_prescoper(field="organization"):
    def prescoper(queryset, info):
        return build_prescoped_queryset(info, queryset, field=field)

    return prescoper


DESCRIPTORS_DESCRIPTION = (
    "This object's descriptors, a flat mapping of key to value: the facts about it that an action's port can `require` and a trigger can test "
    "(e.g. `@fluss/status`). The keys are the ones fluss declares for this structure, and the values are the ones a signal about the object carries. "
    "Empty for a structure that declares none"
)


def resolve_descriptors(root) -> JSON:  # noqa: ANN001 - the model instance behind any hosted type
    """The descriptors of a hosted object, from its structure's declaration (``fluss_server.service``)."""
    from fluss_server.service import service  # the declaration imports reaktion.models

    return service.describe(root)


class PositionModel(BaseModel):
    x: float = Field(description="The horizontal position of the node on the editor canvas.")
    y: float = Field(description="The vertical position of the node on the editor canvas.")


@pydantic.type(PositionModel, description="The 2D canvas position (x, y) of a node in the flow editor.")
class Position:
    x: float
    y: float


class GraphNodeModel(BaseModel):
    kind: enums.GraphNodeKind = Field(description="The kind of node, discriminating the concrete node type.")
    id: str = Field(description="The id of the node, unique within the graph.")
    position: PositionModel = Field(description="The position of the node on the editor canvas.")
    parent_node: str | None = Field(default=None, description="The id of the parent node, if this node is nested inside another.")
    ins: list[list[rmodels.ArgPortModel]] = Field(default_factory=list, description="The input port streams the node consumes (a list of streams, each a list of ports).")
    outs: list[list[rmodels.ReturnPortModel]] = Field(default_factory=list, description="The output port streams the node produces (a list of streams, each a list of ports).")
    constants: list[rmodels.ArgPortModel] = Field(default_factory=list, description="The constant ports configured on the node.")
    voids: list[rmodels.ArgPortModel] = Field(default_factory=list, description="The void ports of the node (neither streamed in nor out).")
    constants_map: Dict[str, Any] = Field(default_factory=dict, description="A map of constant port keys to their configured values.")
    globals_map: Dict[str, Any] = Field(default_factory=dict, description="A map of global argument keys to the node port keys they feed.")
    description: str | None = Field(default=None, description="A human-readable description of what the node does.")
    title: str | None = Field(default=None, description="A human-readable title for the node.")


@pydantic.interface(
    GraphNodeModel,
    description=(
        "A node in a flow graph. This is the common interface implemented by "
        "every concrete node kind (args, returns, reactive, rekuest map/filter, "
        "agent subflow), carrying its id, kind, canvas position and port streams."
    ),
)
class GraphNode:
    id: strawberry.ID
    kind: enums.GraphNodeKind
    position: Position
    parent_node: str | None = None
    ins: list[list[rtypes.ArgPort]]  # Itmes that are streamed in
    outs: list[list[rtypes.ReturnPort]]  # Items that are streamed out
    constants: list[rtypes.ArgPort]  # Items that are constants
    voids: list[rtypes.ArgPort]  # Items that are voids
    constants_map: scalars.ValueMap
    globals_map: scalars.ValueMap
    description: str | None = None
    title: str | None = None


class RetriableNodeModel(BaseModel):
    retries: int = Field(description="The number of times to retry the node on failure.")
    retry_delay: int = Field(description="The delay in milliseconds between retries.")


@pydantic.interface(
    RetriableNodeModel,
    description="Interface for nodes that can retry on failure, carrying the retry count and delay.",
)
class RetriableNode:
    retries: int | None
    retry_delay: int | None


class AssignableNodeModel(BaseModel):
    next_timeout: int | None = Field(description="The timeout in milliseconds to wait for the assigned work before failing.")


@pydantic.interface(
    AssignableNodeModel,
    description="Interface for nodes that assign work to an agent, carrying the assignment timeout.",
)
class AssignableNode:
    next_timeout: int | None


class RekuestActionNodeModel(BaseModel):
    hash: str = Field(description="The hash of the rekuest action this node invokes.")
    map_strategy: str = Field(description="The strategy used to map the input stream onto the action (e.g. MAP, MAP_TO, MAP_FROM).")
    allow_local_execution: bool = Field(description="Whether the action may be executed locally instead of being assigned to an agent.")
    action_kind: str = Field(description="The kind of the rekuest action (e.g. function or generator).")


@pydantic.interface(
    RekuestActionNodeModel,
    description=(
        "Interface for nodes that invoke a rekuest action, carrying the action "
        "hash, the map strategy and whether local execution is allowed."
    ),
)
class RekuestActionNode:
    hash: str
    map_strategy: str
    allow_local_execution: bool
    action_kind: renums.ActionKind


class RekuestMapActionNodeModel(GraphNodeModel, RetriableNodeModel, AssignableNodeModel, RekuestActionNodeModel):
    kind: Literal["REKUEST_MAP"]
    hello: str | None = Field(default=None, description="A placeholder field used to disambiguate this node type in the schema.")


class RekuestFilterActionNodeModel(GraphNodeModel, RetriableNodeModel, AssignableNodeModel, RekuestActionNodeModel):
    kind: Literal["REKUEST_FILTER"]
    path: str | None = Field(default=None, description="A placeholder field used to disambiguate this node type in the schema.")


@pydantic.type(
    RekuestMapActionNodeModel,
    description="A node that maps a rekuest action over its input stream, producing one output per input.",
)
class RekuestMapActionNode(GraphNode, RetriableNode, AssignableNode, RekuestActionNode):
    hello: str | None = None


@pydantic.type(
    RekuestFilterActionNodeModel,
    description="A node that uses a rekuest action as a predicate to filter its input stream.",
)
class RekuestFilterActionNode(GraphNode, RetriableNode, AssignableNode, RekuestActionNode):
    path: str | None = None


class ArgNodeModel(GraphNodeModel):
    kind: Literal["ARGS"]
    arg_stuff: str | None = Field(default=None, description="A placeholder field specific to the args node.")


@pydantic.type(
    ArgNodeModel,
    description="The entry node of a flow: it provides the flow's arguments as the initial output stream.",
)
class ArgNode(GraphNode):
    arg_stuff: str | None = None


class ReactiveNodeModel(GraphNodeModel):
    kind: Literal["REACTIVE"]
    implementation: enums.ReactiveImplementation = Field(description="The reactive operator this node runs (e.g. ZIP, COMBINELATEST, FILTER).")


@pydantic.type(
    ReactiveNodeModel,
    description="A node that runs a built-in reactive operator (the implementation) over its input streams.",
)
class ReactiveNode(GraphNode):
    arg_stuff: str | None = None
    implementation: enums.ReactiveImplementation


class ReturnNodeModel(GraphNodeModel):
    kind: Literal["RETURNS"]
    return_stuff: str | None = Field(default=None, description="A placeholder field specific to the returns node.")


@pydantic.type(
    ReturnNodeModel,
    description="The exit node of a flow: the values it receives become the flow's return values.",
)
class ReturnNode(GraphNode):
    return_stuff: str | None = None


class AgentSubFlowNodeModel(GraphNodeModel):
    kind: Literal["AGENT_SUBFLOW"]
    app_filter: str | None = Field(default=None, description="Restrict the agent to a specific app.")
    version_filter: str | None = Field(default=None, description="Restrict the agent to a specific app version.")
    device_filter: str | None = Field(default=None, description="Restrict the agent to a specific device.")
    instance_filter: str | None = Field(default=None, description="Restrict the agent to a specific instance.")
    user_filter: str | None = Field(default=None, description="Restrict the agent to one owned by a specific user.")
    auto_resolvable: bool = Field(
        default=False,
        description="Whether this dependency is auto resolvable. If so the system will try to automatically resolve a matching agent based on the demands of the dependency and the capabilities of available agents.",
    )


@pydantic.type(
    AgentSubFlowNodeModel,
    description=(
        "A node that delegates a sub-flow to an agent selected by the app / "
        "version / device / user / instance filters, optionally auto-resolving "
        "the matching agent."
    ),
)
class AgentSubFlowNode(GraphNode):
    app_filter: str | None = None
    version_filter: str | None = None
    device_filter: str | None = None
    instance_filter: str | None = None
    user_filter: str | None = None
    auto_resolvable: bool = False


GraphNodeModelUnion = Union[
    RekuestMapActionNodeModel,
    ReactiveNodeModel,
    ArgNodeModel,
    ReturnNodeModel,
    RekuestFilterActionNodeModel,
    AgentSubFlowNodeModel,
]


class StreamItemModel(BaseModel):
    kind: str = Field(description="The port kind of the value carried at this position of the stream.")
    label: str | None = Field(default=None, description="A human-readable label for the value carried at this position of the stream.")


@pydantic.type(
    StreamItemModel,
    description="A single item carried on an edge's stream, describing the port kind and a label of the value that flows through.",
)
class StreamItem:
    kind: renums.PortKind
    label: str


class GraphEdgeModel(BaseModel):
    kind: str = Field(description="The kind of edge, discriminating the concrete edge type (VANILLA or LOGGING).")
    id: str = Field(description="The id of the edge, unique within the graph.")
    source: str = Field(description="The id of the source node.")
    target: str = Field(description="The id of the target node.")
    source_handle: str = Field(description="The handle (port) on the source node the edge leaves from.")
    target_handle: str = Field(description="The handle (port) on the target node the edge arrives at.")
    stream: list[StreamItemModel] = Field(description="The ordered items (the shape of the data) that flow across this edge.")


@pydantic.interface(
    GraphEdgeModel,
    description=(
        "An edge connecting a source node handle to a target node handle in a "
        "flow graph. The common interface for all edge kinds, carrying the "
        "stream of items that flow across it."
    ),
)
class GraphEdge:
    stream: list[StreamItem]
    id: strawberry.ID
    kind: enums.GraphEdgeKind
    source: str
    target: str
    source_handle: str
    target_handle: str


class VanillaEdgeModel(GraphEdgeModel):
    kind: Literal["VANILLA"]
    label: str | None = Field(default=None, description="An optional label shown on the edge in the editor.")


class LoggingEdgeModel(GraphEdgeModel):
    kind: Literal["LOGGING"]
    level: str = Field(description="The log level at which items crossing this edge are logged.")


@pydantic.type(
    VanillaEdgeModel,
    description="A plain edge that streams items from a source handle to a target handle.",
)
class VanillaEdge(GraphEdge):
    label: str | None = None


@pydantic.type(
    LoggingEdgeModel,
    description="An edge that, in addition to streaming items, logs them at the configured level for debugging.",
)
class LoggingEdge(GraphEdge):
    level: str


StreamEdgeModelUnion = Union[VanillaEdgeModel, LoggingEdgeModel]


class GlobalArgModel(BaseModel):
    key: str = Field(description="The key identifying this global argument within the graph.")
    port: rmodels.ArgPortModel = Field(description="The argument port describing the type and widget of the global value.")


@pydantic.type(
    GlobalArgModel,
    description="A graph-level global argument: a named port whose value is shared across the whole flow.",
)
class GlobalArg:
    key: str
    port: rtypes.ArgPort


class GraphModel(BaseModel):
    zoom: str | None = Field(default=None, description="The zoom level of the flow editor when the graph was saved.")
    nodes: list[GraphNodeModelUnion] = Field(description="All nodes in the graph.")
    edges: list[StreamEdgeModelUnion] = Field(description="All edges connecting the nodes in the graph.")
    globals: list[GlobalArgModel] = Field(description="The graph-level global arguments shared across nodes.")


@pydantic.type(
    GraphModel,
    description=(
        "The full definition of a flow: its nodes, the edges connecting them, "
        "the graph-level global arguments and the editor zoom level. This is the "
        "serialized form stored on a Flow."
    ),
)
class Graph:
    zoom: float
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    globals: list[GlobalArg]


@kante.django_type(
    models.Flow,
    filters=filters.FlowFilter,
    ordering=order.FlowOrder,
    pagination=True,
    description=(
        "A Flow is a versioned, executable graph of nodes and edges that lives "
        "inside a Workspace. It is the concrete definition that Runs (live "
        "executions) and Traces (dry runs) are created from. Flows with the same "
        "graph hash within a workspace are deduplicated."
    ),
)
class Flow:
    id: strawberry.ID = kante.django_field(description="The unique identifier of the flow.")
    descriptors: JSON = kante.django_field(resolver=resolve_descriptors, description=DESCRIPTORS_DESCRIPTION)
    title: str = kante.django_field(description="A human-readable title for the flow.")
    description: str | None = kante.django_field(description="An optional longer description of what the flow does.")
    created_at: datetime.datetime = kante.django_field(description="The time at which the flow was created.")
    workspace: "Workspace" = kante.django_field(description="The workspace this flow belongs to.")
    hash: str = kante.django_field(description="A content hash of the graph, used to deduplicate identical flows within a workspace.")

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return build_prescoped_queryset(info, queryset)

    @kante.django_field(description="The full node-and-edge graph (nodes, edges and globals) that defines the flow.")
    def graph(self, info: Info) -> Graph:
        return GraphModel(**self.graph)


@kante.django_type(
    models.Workspace,
    filters=filters.WorkspaceFilter,
    ordering=order.WorkspaceOrder,
    pagination=True,
    description=(
        "A Workspace is the top-level container that groups the Flows of an "
        "organization, mirroring the concept of a project or folder. It is the "
        "entry point users edit flows within."
    ),
)
class Workspace:
    id: strawberry.ID = kante.django_field(description="The unique identifier of the workspace.")
    descriptors: JSON = kante.django_field(resolver=resolve_descriptors, description=DESCRIPTORS_DESCRIPTION)
    title: str = kante.django_field(description="A human-readable title for the workspace.")
    description: str | None = kante.django_field(description="An optional longer description of the workspace.")
    created_at: datetime.datetime = kante.django_field(description="The time at which the workspace was created.")
    flows: list["Flow"] = kante.django_field(description="All flows contained in this workspace.")

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return build_prescoped_queryset(info, queryset)

    @kante.django_field(description="The most recently created flow in this workspace, if any.")
    def latest_flow(self, info: Info) -> Optional[Flow]:
        return self.flows.order_by("-created_at").first()


class ManifestEntryModel(BaseModel):
    alias: str = Field(description="The name the action is injected under in the source.")
    action_hash: str = Field(description="The hash of the action definition that is called.")
    app: str | None = Field(default=None, description="The app that provides the action, if pinned.")
    key: str | None = Field(default=None, description="The key of the action within its app, if pinned.")
    version: str | None = Field(default=None, description="The version of the app, if pinned.")
    effect: renums.EffectClass = Field(default=renums.EffectClass.NONE, description="Whether calling the action touches the real world (PHYSICAL).")


@pydantic.type(ManifestEntryModel, description="One action a Python flow may call. The manifest is the flow's permission boundary: the executor injects only these.")
class ManifestEntry:
    alias: str
    action_hash: str
    app: str | None
    key: str | None
    version: str | None
    effect: renums.EffectClass


@kante.django_type(
    models.PythonFlow,
    filters=filters.PythonFlowFilter,
    ordering=order.PythonFlowOrder,
    pagination=True,
    description=(
        "A PythonFlow is one immutable version of a flow written as Python source. Versions of the "
        "same flow share a lineage; identical content within a lineage is deduplicated. Only "
        "PUBLISHED versions are registered as actions."
    ),
)
class PythonFlow:
    id: strawberry.ID = kante.django_field(description="The unique identifier of this version.")
    descriptors: JSON = kante.django_field(resolver=resolve_descriptors, description=DESCRIPTORS_DESCRIPTION)
    title: str = kante.django_field(description="A human-readable title for the flow.")
    description: str | None = kante.django_field(description="An optional longer description of what the flow does.")
    created_at: datetime.datetime = kante.django_field(description="The time at which this version was created.")
    lineage: strawberry.ID = kante.django_field(description="Shared by every version of the same flow.")
    previous: Optional["PythonFlow"] = kante.django_field(description="The version this one was derived from, if any.")
    next_versions: list["PythonFlow"] = kante.django_field(description="The versions derived from this one.")
    source: str = kante.django_field(description="The Python source of the flow.")
    entrypoint: str = kante.django_field(description="The function in the source that is called.")
    runtime: str = kante.django_field(description="The executor runtime (interpreter + helpers) the source was validated against.")
    status: enums.PythonFlowStatus = kante.django_field(description="DRAFT, PUBLISHED (registered as an action) or ARCHIVED.")
    hash: str = kante.django_field(description="A content hash over source, entrypoint, manifest and runtime.")
    runs: list["PythonRun"] = kante.django_field(description="The runs of this version.")

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return build_prescoped_queryset(info, queryset)

    @kante.django_field(description="The arguments of the entrypoint, as rekuest ports.")
    def args(self, info: Info) -> list[rtypes.ArgPort]:
        return [rmodels.ArgPortModel(**port) for port in self.args]

    @kante.django_field(description="The return values of the entrypoint, as rekuest ports.")
    def returns(self, info: Info) -> list[rtypes.ReturnPort]:
        return [rmodels.ReturnPortModel(**port) for port in self.returns]

    @kante.django_field(description="Every action the source may call, under the name it is injected as.")
    def manifest(self, info: Info) -> list[ManifestEntry]:
        return [ManifestEntryModel(**entry) for entry in self.manifest]

    @kante.django_field(description="Whether any action in the manifest has a PHYSICAL effect.")
    def physical(self, info: Info) -> bool:
        return self.is_physical

    @kante.django_field(description="Every version in this flow's lineage, oldest first.")
    def versions(self, info: Info) -> list["PythonFlow"]:
        return list(models.PythonFlow.objects.filter(organization_id=self.organization_id, lineage=self.lineage).order_by("created_at", "id"))


@kante.django_type(
    models.PythonRun,
    filters=filters.PythonRunFilter,
    ordering=order.PythonRunOrder,
    pagination=True,
    description="A PythonRun is one execution of a published PythonFlow for a task; its step-by-step history is that task's child tasks in rekuest.",
)
class PythonRun:
    id: strawberry.ID = kante.django_field(description="The unique identifier of the run.")
    descriptors: JSON = kante.django_field(resolver=resolve_descriptors, description=DESCRIPTORS_DESCRIPTION)
    flow: PythonFlow = kante.django_field(description="The version that is executed.")
    task_id: strawberry.ID = kante.django_field(description="The id of the rekuest task that runs the flow.")
    status: enums.PythonRunStatus = kante.django_field(description="RUNNING, COMPLETED or FAILED.")
    created_at: datetime.datetime = kante.django_field(description="The time at which the run started.")
    finished_at: datetime.datetime | None = kante.django_field(description="The time at which the run finished, if it has.")

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return build_prescoped_queryset(info, queryset, field="flow__organization")


WorkspaceStats, WorkspaceStatsResolver = create_stats_type(
    model=models.Workspace,
    filters=filters.WorkspaceFilter,
    allowed_fields={
        "created_at": "created_at",
    },
    allowed_datetime_fields={"created_at": "created_at"},
    prescope=build_prescoper(field="organization"),
)


@kante.django_type(
    models.ReactiveTemplate,
    filters=filters.ReactiveTemplateFilter,
    ordering=order.ReactiveTemplateOrder,
    pagination=True,
    description=(
        "A ReactiveTemplate is a reusable, global catalog entry describing a "
        "reactive operator — its implementation (zip, combine-latest, chunk, "
        "filter, arithmetic, …) together with its input/output port streams and "
        "constants. Reactive nodes in a flow instantiate one of these templates."
    ),
)
class ReactiveTemplate:
    id: strawberry.ID = kante.django_field(description="The unique identifier of the reactive template.")
    implementation: enums.ReactiveImplementation = kante.django_field(description="The reactive operator this template implements (e.g. ZIP, COMBINELATEST, FILTER).")
    title: str = kante.django_field(description="A human-readable title for the template.")
    description: str | None = kante.django_field(description="An optional longer description of the operator's behaviour.")

    @kante.django_field(description="The input port streams the operator consumes (a list of streams, each a list of argument ports).")
    def ins(self, info: Info) -> list[list[rtypes.ArgPort]]:
        return [[rmodels.ArgPortModel(**i) for i in stream] for stream in self.ins]

    @kante.django_field(description="The output port streams the operator produces (a list of streams, each a list of return ports).")
    def outs(self, info: Info) -> list[list[rtypes.ReturnPort]]:
        return [[rmodels.ReturnPortModel(**i) for i in stream] for stream in self.outs]

    @kante.django_field(description="The constant argument ports configured on the operator.")
    def constants(self, info: Info) -> list[rtypes.ArgPort]:
        return [rmodels.ArgPortModel(**i) for i in self.constants]

    @kante.django_field(description="The void ports of the operator (ports that neither stream in nor out).")
    def voids(self, info: Info) -> list[rtypes.ArgPort]:
        return []


@kante.django_type(
    models.Run,
    filters=filters.RunFilter,
    ordering=order.RunOrder,
    pagination=True,
    description=(
        "A Run is a single live execution of a Flow, tied to a task. As "
        "it executes it accumulates RunEvents (per-node values, errors and "
        "completions) and periodic Snapshots that capture its state over time."
    ),
)
class Run:
    id: strawberry.ID = kante.django_field(description="The unique identifier of the run.")
    descriptors: JSON = kante.django_field(resolver=resolve_descriptors, description=DESCRIPTORS_DESCRIPTION)
    created_at: datetime.datetime = kante.django_field(description="The time at which the run was started.")
    events: list["RunEvent"] = kante.django_field(description="All events emitted during this run, in order.")
    flow: "Flow" = kante.django_field(description="The flow that is being executed by this run.")
    task_id: strawberry.ID = kante.django_field(description="The id of the task that triggered this run.")
    snapshots: list["Snapshot"] = kante.django_field(description="The state snapshots captured during this run.")
    status: enums.RunStatus = kante.django_field(description="The current status of the run (RUNNING or COMPLETED).")

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return build_prescoped_queryset(info, queryset, field="flow__organization")

    @kante.django_field(description="The most recent state snapshot of this run, if any.")
    def latest_snapshot(self, info: Info) -> Optional["Snapshot"]:
        return self.snapshots.order_by("-created_at").first()


@kante.django_type(
    models.Snapshot,
    filters=filters.SnapshotFilter,
    ordering=order.SnapshotOrder,
    pagination=True,
    description=(
        "A Snapshot captures the state of a Run at a logical time `t`, grouping "
        "the events that were active at that point so a client can reconstruct "
        "the run's state without replaying every event."
    ),
)
class Snapshot:
    t: int = kante.django_field(description="The logical time of the run at which this snapshot was taken.")
    run: "Run" = kante.django_field(description="The run this snapshot belongs to.")
    events: list["RunEvent"] = kante.django_field(description="The events that were active at the snapshot's logical time.")
    id: strawberry.ID = kante.django_field(description="The unique identifier of the snapshot.")
    status: str | None = kante.django_field(description="An optional status label describing the run state at this snapshot.")
    created_at: datetime.datetime = kante.django_field(description="The wall-clock time at which the snapshot was taken.")

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return build_prescoped_queryset(info, queryset, field="run__flow__organization")


@kante.django_type(
    models.RunEvent,
    filters=filters.RunEventFilter,
    ordering=order.RunEventOrder,
    pagination=True,
    description=(
        "A RunEvent is a single event emitted while a Run executes: a streamed "
        "value (NEXT), an ERROR, or a COMPLETE, originating from a specific node "
        "handle in the flow."
    ),
)
class RunEvent:
    id: strawberry.ID = kante.django_field(description="The unique identifier of the event.")
    t: int = kante.django_field(description="The logical time of the run at which this event was emitted.")
    caused_by: list[strawberry.ID] = kante.django_field(description="The ids of the events that caused this event (its causal parents).")
    value: scalars.EventValue | None = kante.django_field(description="The payload of the event (the streamed value, or the exception for an ERROR).")
    exception: str | None = kante.django_field(description="A human-readable exception message, set for ERROR events.")
    kind: enums.RunEventKind = kante.django_field(description="The kind of event: NEXT, ERROR, COMPLETE or UNKNOWN.")
    handle: str = kante.django_field(description="The node handle (port) the event was emitted on.")
    source: str = kante.django_field(description="The id of the node that emitted the event.")
    created_at: datetime.datetime = kante.django_field(description="The wall-clock time at which the event was recorded.")

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return build_prescoped_queryset(info, queryset, field="run__flow__organization")


@kante.django_type(
    models.Trace,
    filters=filters.TraceFilter,
    ordering=order.TraceOrder,
    pagination=True,
    description=(
        "A Trace records a provisioning / dry-run execution of a Flow — its "
        "events and snapshots — used to debug or validate a flow without "
        "performing a full Run."
    ),
)
class Trace:
    id: strawberry.ID = kante.django_field(description="The unique identifier of the trace.")


@kante.django_type(
    models.TraceSnapshot,
    filters=filters.TraceSnapshotFilter,
    ordering=order.TraceSnapshotOrder,
    pagination=True,
    description="A TraceSnapshot captures the state of a Trace at a point in time.",
)
class TraceSnapshot:
    id: strawberry.ID = kante.django_field(description="The unique identifier of the trace snapshot.")


@kante.django_type(
    models.TraceEvent,
    filters=filters.TraceEventFilter,
    ordering=order.TraceEventOrder,
    pagination=True,
    description="A TraceEvent is a single event emitted during a Trace.",
)
class TraceEvent:
    id: strawberry.ID = kante.django_field(description="The unique identifier of the trace event.")

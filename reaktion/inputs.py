import keyword
from strawberry.experimental import pydantic
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator
from rekuest_core.inputs import models as rimodels
from rekuest_core.inputs import types as ritypes
from rekuest_core import enums as renums
from reaktion import scalars, enums
from typing import Annotated, Any, Dict, Optional, cast
from strawberry import LazyType
import strawberry


def _map_or_empty(value: Any) -> Any:
    """Treat an omitted (``null``) map as an empty one.

    ``ValueMapInput`` fields must default to *null* rather than ``{}`` on the wire:
    ``ValueMap`` is a custom scalar, and graphql-js cannot turn an object default back
    into an AST literal, so an ``= {}`` default makes both ``printSchema`` and
    introspection raise ``Cannot convert value to AST: {}`` and breaks client codegen.
    The stored graph still always carries a map -- the matching output fields on
    ``GraphNode`` are non-null -- so normalise ``None`` back to ``{}`` here.
    """
    return {} if value is None else value


#: A map-valued input field that is optional on the wire but always a dict in Python.
ValueMapInput = Annotated[Dict[str, Any], BeforeValidator(_map_or_empty)]

#: Default for a ``ValueMapInput``. It is ``None`` at runtime -- which is what makes
#: strawberry emit ``= null`` rather than ``= {}`` in the SDL -- and ``validate_default``
#: then runs ``_map_or_empty`` over it, so the model still lands a dict. Cast because the
#: declared field type is the post-validation ``Dict``, not the on-the-wire ``None``.
#:
#: This has to live on the *pydantic* model: ``strawberry.experimental.pydantic`` derives
#: every SDL default from the pydantic FieldInfo and ignores whatever default is written on
#: the decorated strawberry class, so setting ``= None``/``= strawberry.UNSET`` over on
#: ``GraphNodeInput`` has no effect. And it has to be ``None`` specifically: strawberry's
#: ``get_default_factory_for_field`` treats a ``None`` default as "no default" and falls
#: through to emitting null, while any ``default_factory`` (such as ``dict``) is emitted
#: verbatim -- which is what produced the unrepresentable ``= {}``.
OMITTED_MAP: ValueMapInput = cast(ValueMapInput, cast(object, None))


class PositionInputModel(BaseModel):
    x: float
    y: float


@pydantic.input(PositionInputModel)
class PositionInput:
    x: float
    y: float


class GraphNodeInputModel(BaseModel):
    id: str
    kind: enums.GraphNodeKind
    position: PositionInputModel
    parent_node: str | None = None
    ins: list[list[rimodels.ArgPortInputModel]] | None = None  # A set of streams
    outs: list[list[rimodels.ReturnPortInputModel]] | None = None
    constants: list[rimodels.ArgPortInputModel] | None = None
    voids: list[rimodels.ArgPortInputModel] = Field(default_factory=list)
    constants_map: ValueMapInput = Field(default=OMITTED_MAP, validate_default=True)
    globals_map: ValueMapInput = Field(default=OMITTED_MAP, validate_default=True)
    description: str | None = None
    title: str | None = None
    retries: int | None = None
    retry_delay: int | None = None
    action_kind: renums.ActionKind | None = None
    next_timeout: int | None = None
    hash: str | None = None
    map_strategy: enums.MapStrategy | None = None
    allow_local_execution: bool | None = None
    binds: rimodels.BindsInputModel | None = None
    implementation: enums.ReactiveImplementation | None = None
    app_filter: str | None = None
    version_filter: str | None = None
    device_filter: str | None = None
    user_filter: str | None = None
    instance_filter: str | None = None
    auto_resolvable: bool = False


@pydantic.input(GraphNodeInputModel)
class GraphNodeInput:
    id: str
    kind: enums.GraphNodeKind
    position: PositionInput
    parent_node: str | None = None
    ins: list[list[ritypes.ArgPortInput]] | None = None  # A set of streams
    outs: list[list[ritypes.ReturnPortInput]] | None = None
    constants: list[ritypes.ArgPortInput] | None = None
    voids: list[ritypes.ArgPortInput] | None = None
    constants_map: scalars.ValueMap | None = None
    globals_map: scalars.ValueMap | None = None
    description: str | None = None
    title: str | None = None
    retries: int | None = None
    retry_delay: int | None = None
    action_kind: renums.ActionKind | None = None
    next_timeout: int | None = None
    hash: str | None = None
    map_strategy: enums.MapStrategy | None = None
    allow_local_execution: bool | None = None
    parent_node: str | None = None
    implementation: enums.ReactiveImplementation | None = None
    # Placeholder for the node kind
    hello: str | None = None
    path: str | None = None
    app_filter: str | None = None
    version_filter: str | None = None
    device_filter: str | None = None
    user_filter: str | None = None
    instance_filter: str | None = None
    auto_resolvable: bool = strawberry.field(
        default=False,
        description="Whether this dependency is auto resolvable or not. If so we will try to automatically resolve it based on the demands specified in the dependency and the capabilities of the available agents in the system. This is used to identify the demand in the system. Attention if any of the dependencies of this agent dependency is not auto resolvable, this dependency will also not be auto resolvable",
    )


class StreamItemInputModel(BaseModel):
    kind: str
    label: str | None = None


@pydantic.input(StreamItemInputModel)
class StreamItemInput:
    kind: renums.PortKind
    label: str


class GraphEdgeInputModel(BaseModel):
    kind: str
    id: str
    source: str
    target: str
    source_handle: str
    target_handle: str
    stream: list[StreamItemInputModel]


@pydantic.input(GraphEdgeInputModel)
class GraphEdgeInput:
    kind: enums.GraphEdgeKind
    id: str
    source: str
    target: str
    source_handle: str
    target_handle: str
    stream: list[StreamItemInput]
    label: str | None = None
    level: str | None = None


class GlobalArgInputModel(BaseModel):
    key: str
    port: rimodels.ArgPortInputModel


@pydantic.input(GlobalArgInputModel)
class GlobalArgInput:
    key: str
    port: ritypes.ArgPortInput


class GraphInputModel(BaseModel):
    nodes: list[GraphNodeInputModel]
    edges: list[GraphEdgeInputModel]
    globals: list[GlobalArgInputModel]


@pydantic.input(GraphInputModel)
class GraphInput:
    nodes: list[GraphNodeInput]
    edges: list[GraphEdgeInput]
    globals: list[GlobalArgInput]


class ReactiveTemplateInputModel(BaseModel):
    title: str
    description: str
    ins: list[list[rimodels.ArgPortInputModel]]  # A set of streams
    outs: list[list[rimodels.ReturnPortInputModel]]
    constants: list[rimodels.ArgPortInputModel]
    implementation: enums.ReactiveImplementation

    model_config = ConfigDict(use_enum_values=True)


@pydantic.input(ReactiveTemplateInputModel, all_fields=True)
class ReactiveTemplateInput:
    title: str
    description: str
    ins: list[list[ritypes.ArgPortInput]]  # A set of streams
    outs: list[list[ritypes.ReturnPortInput]]
    constants: list[ritypes.ArgPortInput]
    implementation: enums.ReactiveImplementation


@strawberry.input
class PortMatchInput:
    at: int | None = None
    key: str | None = None
    kind: renums.PortKind | None = None
    identifier: str | None = None
    nullable: bool | None = None
    variants: Optional[list[LazyType["PortDemandInput", __name__]]] = None
    child: Optional[LazyType["PortDemandInput", __name__]] = None


@strawberry.input
class PortDemandInput:
    kind: enums.DemandKind
    matches: list[PortMatchInput] | None = None
    force_length: int | None = None
    force_non_nullable_length: int | None = None


class CreateRunInputModel(BaseModel):
    flow: str
    snapshot_interval: int
    task_id: str


class CloseRunInputModel(BaseModel):
    run: str


@pydantic.input(CloseRunInputModel)
class CloseRunInput:
    run: strawberry.ID


@pydantic.input(CreateRunInputModel)
class CreateRunInput:
    task_id: strawberry.ID
    flow: strawberry.ID
    snapshot_interval: int


class DeteteRunInputModel(BaseModel):
    run: str


@pydantic.input(DeteteRunInputModel)
class DeleteRunInput:
    run: strawberry.ID


class SnapshotRunInputModel(BaseModel):
    run: str
    events: list[str]
    t: int


@pydantic.input(SnapshotRunInputModel)
class SnapshotRunInput:
    run: strawberry.ID
    events: list[strawberry.ID]
    t: int


class DeleteSnapshotInputModel(BaseModel):
    snapshot: str


@pydantic.input(DeleteSnapshotInputModel)
class DeleteSnapshotInput:
    snapshot: strawberry.ID


class TrackInputModel(BaseModel):
    reference: str
    t: int
    kind: str
    value: Any | None = None
    run: strawberry.ID
    caused_by: list[str] = Field(default_factory=list)
    message: str | None = None
    exception: str | None = None
    source: str | None = None
    handle: str | None = None


@pydantic.input(TrackInputModel)
class TrackInput:
    reference: str
    t: int
    kind: enums.RunEventKind
    value: scalars.EventValue | None = None
    exception: str | None = None
    run: strawberry.ID
    caused_by: list[strawberry.ID]
    message: str | None = None
    source: str | None = None
    handle: str | None = None


# --- Python flows ------------------------------------------------------------------------


class ManifestEntryInputModel(BaseModel):
    alias: str = Field(description="The name the action is injected under in the source")
    action_hash: str
    app: str | None = None
    key: str | None = None
    version: str | None = None
    effect: renums.EffectClass = renums.EffectClass.NONE

    @field_validator("alias")
    @classmethod
    def _alias_is_an_identifier(cls, value: str) -> str:
        if not value.isidentifier() or keyword.iskeyword(value):
            raise ValueError(f"A manifest alias must be a Python identifier, not {value!r}")
        return value


@pydantic.input(ManifestEntryInputModel, description="One action a Python flow may call, as the executor's validation resolved it.")
class ManifestEntryInput:
    alias: str
    action_hash: str
    app: str | None = None
    key: str | None = None
    version: str | None = None
    effect: renums.EffectClass = renums.EffectClass.NONE


class CreatePythonFlowInputModel(BaseModel):
    source: str
    entrypoint: str = "main"
    title: str | None = None
    description: str | None = None
    previous: str | None = None
    args: list[rimodels.ArgPortInputModel] = Field(default_factory=list)
    returns: list[rimodels.ReturnPortInputModel] = Field(default_factory=list)
    manifest: list[ManifestEntryInputModel] = Field(default_factory=list)
    runtime: str

    @field_validator("entrypoint")
    @classmethod
    def _entrypoint_is_an_identifier(cls, value: str) -> str:
        if not value.isidentifier():
            raise ValueError(f"The entrypoint must be a Python identifier, not {value!r}")
        return value

    @field_validator("manifest")
    @classmethod
    def _aliases_are_unique(cls, value: list[ManifestEntryInputModel]) -> list[ManifestEntryInputModel]:
        aliases = [entry.alias for entry in value]
        duplicates = sorted({alias for alias in aliases if aliases.count(alias) > 1})
        if duplicates:
            raise ValueError(f"Manifest aliases must be unique; duplicated: {', '.join(duplicates)}")
        return value


@pydantic.input(CreatePythonFlowInputModel, description="A new PythonFlow version, carrying the report the executor's validation produced for its source.")
class CreatePythonFlowInput:
    source: str
    entrypoint: str = "main"
    title: str | None = None
    description: str | None = None
    previous: strawberry.ID | None = None
    args: list[ritypes.ArgPortInput]
    returns: list[ritypes.ReturnPortInput]
    manifest: list[ManifestEntryInput]
    runtime: str


@strawberry.input(description="Change a PythonFlow's title or description; its source, manifest and runtime are immutable.")
class UpdatePythonFlowInput:
    id: strawberry.ID
    title: str | None = None
    description: str | None = None


@strawberry.input(description="Refers to one PythonFlow version.")
class PythonFlowRefInput:
    id: strawberry.ID


@strawberry.input(description="Start (or reuse) the run of a published PythonFlow for a task.")
class CreatePythonRunInput:
    flow: strawberry.ID
    task_id: strawberry.ID


@strawberry.input(description="Finish a PythonRun.")
class ClosePythonRunInput:
    run: strawberry.ID
    status: enums.PythonRunStatus = enums.PythonRunStatus.COMPLETED

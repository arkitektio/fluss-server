import logging

import strawberry
from kante.types import Info

from reaktion import inputs, models, types
from reaktion.hashers import hash_graph
from reaktion.scoping import get_for_org

logger = logging.getLogger(__name__)


@strawberry.input
class UpdateWorkspaceInput:
    workspace: strawberry.ID
    graph: inputs.GraphInput
    title: str | None = None
    description: str | None = None


def update_workspace(info: Info, input: UpdateWorkspaceInput) -> types.Workspace:
    # Scope to the request's organization: only own workspaces can be updated
    # (raises DoesNotExist for a cross-org / unknown workspace).
    workspace = get_for_org(models.Workspace, info, id=input.workspace)

    # Validate through the pydantic graph model (port kinds, widgets, dependencies) and store
    # the normalised dump; the hash is over that dump.
    graph = input.graph.to_pydantic().model_dump(mode="json")

    flow, _ = models.Flow.objects.get_or_create(
        workspace=workspace,
        hash=hash_graph(graph),
        defaults=dict(
            title=input.title or "Untitled Workspace",
            description=input.description or "No description",
            creator=info.context.request.user,
            graph=graph,
            organization=info.context.request.organization,
        ),
    )

    if input.title:
        flow.title = input.title
    if input.description:
        flow.description = input.description

    flow.save()

    return workspace


@strawberry.input
class CreateWorkspaceInput:
    graph: inputs.GraphInput | None = None
    title: str | None = None
    description: str | None = None
    vanilla: bool = False


def create_workspace(info: Info, input: CreateWorkspaceInput) -> types.Workspace:
    title = input.title or "Untitled Workspace"
    workspace = models.Workspace.objects.create(
        title=title,
        description=input.description,
        creator=info.context.request.user,
        organization=info.context.request.organization,
    )

    nodes = [
        {
            "id": "1",
            "kind": "ARGS",
            "ins": [[]],
            "outs": [[]],
            "cons": [],
            "voids": [],
            "position": {"x": 0, "y": 50},
            "constants": [],
            "constants_map": {},
            "globals_map": {},
            "title": "Input",
            "description": "The input to the workflow",
        },
        {
            "id": "2",
            "kind": "RETURNS",
            "ins": [[]],
            "outs": [[]],
            "cons": [],
            "voids": [],
            "position": {"x": 1500, "y": 50},
            "constants": [],
            "constants_map": {},
            "globals_map": {},
            "title": "Output",
            "description": "The output to the workflow",
        },
    ]

    # The default graph goes through the same validation and normalisation as a posted one.
    graph = inputs.GraphInputModel.model_validate(
        {"nodes": nodes, "edges": [], "globals": []}
    ).model_dump(mode="json")

    models.Flow.objects.create(
        workspace=workspace,
        graph=graph,
        hash=hash_graph(graph),
        title=title,
        description=input.description,
        creator=info.context.request.user,
        organization=info.context.request.organization,
    )

    return workspace

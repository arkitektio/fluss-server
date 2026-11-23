"""A guest of the organization, granted a collaboration and nothing else: what they read, and that they write nothing.

Their token lists their collaborations by key (`collabs`: lok's key, one across the hub), with the
roles they hold in each; the guest token is minted per test. A full member ("test") puts objects in a
collaboration under a fresh key (`addManyToCollaboration`, which makes fluss's row of it); what each
needs to be seen comes along, and what is part of it is in it.
"""

import uuid

import pytest
from arkitekt_service.collaborations.models import Collaboration
from arkitekt_service.service import Service
from asgiref.sync import sync_to_async
from django.db.models import Model
from kante.context import HttpContext
from strawberry.types import ExecutionResult

from fluss_server.schema import schema
from reaktion import models
from tests.conftest import token_context
from tests.utils import (
    GuestFactory,
    MakeFlow,
    MakeRun,
    MakeSnapshot,
    MakeWorkspace,
    data_of,
)

WORKSPACES = "{ workspaces { id flows { id } latestFlow { id } } }"
WORKSPACE = "query ($id: ID!) { workspace(id: $id) { id flows { id } } }"
FLOWS = "{ flows { id } }"
RUNS = "{ runs { id } }"
RENDER_RUN = """
query ($id: ID!) {
  run(id: $id) {
    id
    flow { id workspace { id } }
    events { id }
    snapshots { id events { id } }
    latestSnapshot { id }
  }
}
"""
EVENTS_BETWEEN = "query ($run: ID!) { eventsBetween(run: $run) { id } }"
TRACK = "mutation ($input: TrackInput!) { track(input: $input) { id } }"
CREATE_RUN = "mutation ($input: CreateRunInput!) { createRun(input: $input) { id } }"
CREATE_PYTHON_RUN = (
    "mutation ($input: CreatePythonRunInput!) { createPythonRun(input: $input) { id } }"
)
UPDATE_WORKSPACE = (
    "mutation ($input: UpdateWorkspaceInput!) { updateWorkspace(input: $input) { id } }"
)
ADD = "mutation ($input: CollaborationObjectInput!) { addToCollaboration(input: $input) { key name items { identifier objectId brought } } }"
ADD_MANY = "mutation ($input: AddManyToCollaborationInput!) { addManyToCollaboration(input: $input) { key name } }"


async def _run(ctx: HttpContext, query: str, **variables: object) -> ExecutionResult:
    return await schema.execute(
        query, context_value=ctx, variable_values=variables or None
    )


def _identifier(obj: Model) -> str:
    structure = Service.hosting(obj)
    assert structure is not None, f"{type(obj).__name__} is no structure here"
    return structure.identifier


async def _collaboration(ctx: HttpContext, *objects: Model) -> str:
    """A collaboration of ``ctx``'s organization holding ``objects``, as a full member of it puts them
    in: under a fresh key, as lok hands one out, in one ``addManyToCollaboration``. Its key."""
    key = str(uuid.uuid4())
    member = token_context(str(ctx.request.get_extension("token")))
    added = await _run(
        member,
        ADD_MANY,
        input={
            "collaboration": key,
            "name": "Shared",
            "objects": [
                {"identifier": _identifier(obj), "object": str(obj.pk)}
                for obj in objects
            ],
        },
    )
    assert data_of(added)["addManyToCollaboration"] == {"key": key, "name": "Shared"}
    assert await Collaboration.objects.filter(
        key=key, organization=ctx.request.organization
    ).aexists()
    return key


def _refused(result: ExecutionResult, reason: str) -> None:
    assert result.errors, "it was let through"
    assert result.errors[0].extensions.get("reason") == reason, result.errors


def _ids(rows: list[dict]) -> list[str]:
    return sorted(row["id"] for row in rows)


@sync_to_async
def _event(run: models.Run, t: int) -> models.RunEvent:
    return models.RunEvent.objects.create(
        run=run, t=t, kind="NEXT", source="node-1", handle="out-0"
    )


@sync_to_async
def _python_flow(ctx: HttpContext, title: str) -> models.PythonFlow:
    return models.PythonFlow.objects.create(
        organization=ctx.request.organization,
        creator=ctx.request.user,
        title=title,
        source="async def main() -> None:\n    return None\n",
        runtime="test",
        status="PUBLISHED",
        hash=uuid.uuid4().hex,
    )


@sync_to_async
def _python_run(flow: models.PythonFlow) -> models.PythonRun:
    return models.PythonRun.objects.create(flow=flow, task_id=uuid.uuid4().hex)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_guest_reads_the_workspace_in_their_collaboration_and_its_flows(
    authenticated_context: HttpContext,
    guest: GuestFactory,
    make_workspace: MakeWorkspace,
    make_flow: MakeFlow,
) -> None:
    shared = await make_workspace(title="Shared")
    versions = [
        await make_flow(workspace=shared, title=f"v{index}") for index in range(2)
    ]
    other = await make_workspace(title="Other")
    await make_flow(workspace=other)
    ctx = guest({await _collaboration(authenticated_context, shared): []})

    listed = await _run(ctx, WORKSPACES)
    assert not listed.errors, listed.errors
    assert listed.data is not None
    (workspace,) = listed.data["workspaces"]
    assert workspace["id"] == str(shared.pk)
    assert _ids(workspace["flows"]) == _ids([{"id": str(flow.pk)} for flow in versions])
    assert workspace["latestFlow"] is not None
    assert _ids(data_of(await _run(ctx, FLOWS))["flows"]) == _ids(workspace["flows"])
    assert (await _run(ctx, WORKSPACE, id=str(other.pk))).errors


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_flow_saved_into_a_shared_workspace_later_comes_in(
    authenticated_context: HttpContext,
    guest: GuestFactory,
    make_workspace: MakeWorkspace,
    make_flow: MakeFlow,
) -> None:
    workspace = await make_workspace(title="Growing")
    await make_flow(workspace=workspace, title="v1")
    ctx = guest({await _collaboration(authenticated_context, workspace): []})
    later = await make_flow(workspace=workspace, title="v2")

    seen = await _run(ctx, WORKSPACE, id=str(workspace.pk))
    assert not seen.errors, seen.errors
    assert seen.data is not None
    assert str(later.pk) in [flow["id"] for flow in seen.data["workspace"]["flows"]]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_shared_run_renders_with_its_flow_events_and_snapshots(
    authenticated_context: HttpContext,
    guest: GuestFactory,
    make_run: MakeRun,
    make_snapshot: MakeSnapshot,
) -> None:
    run = await make_run()
    event = await _event(run, t=1)
    snapshot = await make_snapshot(run, t=1)
    await sync_to_async(snapshot.events.add)(event)
    ctx = guest({await _collaboration(authenticated_context, run): []})

    result = await _run(ctx, RENDER_RUN, id=str(run.pk))
    assert not result.errors, result.errors
    assert result.data is not None
    rendered = result.data["run"]
    assert rendered["flow"]["id"] == str(run.flow_id)
    assert rendered["flow"]["workspace"]["id"] is not None
    assert _ids(rendered["events"]) == [str(event.pk)]
    assert rendered["snapshots"] == [
        {"id": str(snapshot.pk), "events": [{"id": str(event.pk)}]}
    ]
    assert rendered["latestSnapshot"]["id"] == str(snapshot.pk)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_an_event_tracked_after_sharing_is_seen(
    authenticated_context: HttpContext, guest: GuestFactory, make_run: MakeRun
) -> None:
    run = await make_run()
    ctx = guest({await _collaboration(authenticated_context, run): []})
    tracked = await _run(
        authenticated_context,
        TRACK,
        input={
            "run": str(run.pk),
            "reference": "ref-1",
            "t": 1,
            "kind": "NEXT",
            "causedBy": [],
            "source": "node-1",
            "handle": "out-0",
        },
    )
    assert not tracked.errors, tracked.errors
    assert tracked.data is not None

    between = await _run(ctx, EVENTS_BETWEEN, run=str(run.pk))
    assert not between.errors, between.errors
    assert between.data is not None
    assert _ids(between.data["eventsBetween"]) == [tracked.data["track"]["id"]]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_sharing_a_workspace_shares_none_of_its_runs(
    authenticated_context: HttpContext,
    guest: GuestFactory,
    make_workspace: MakeWorkspace,
    make_flow: MakeFlow,
    make_run: MakeRun,
) -> None:
    workspace = await make_workspace()
    run = await make_run(flow=await make_flow(workspace=workspace))
    unshared = await make_run()
    ctx = guest({await _collaboration(authenticated_context, workspace): []})

    assert data_of(await _run(ctx, RUNS))["runs"] == []
    assert (await _run(ctx, RENDER_RUN, id=str(run.pk))).errors
    assert (await _run(ctx, EVENTS_BETWEEN, run=str(unshared.pk))).errors


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_python_run_brings_its_flow_and_a_flow_brings_none_of_its_runs(
    authenticated_context: HttpContext, guest: GuestFactory
) -> None:
    flow = await _python_flow(authenticated_context, "Shared")
    run = await _python_run(flow)
    other = await _python_run(flow)

    by_flow = guest({await _collaboration(authenticated_context, flow): []})
    result = await _run(
        by_flow,
        "query ($id: ID!) { pythonFlow(id: $id) { id runs { id } } }",
        id=str(flow.pk),
    )
    assert not result.errors, result.errors
    assert result.data is not None
    assert result.data["pythonFlow"]["runs"] == []
    assert data_of(await _run(by_flow, "{ pythonRuns { id } }"))["pythonRuns"] == []

    by_run = guest({await _collaboration(authenticated_context, run): []})
    listed = await _run(by_run, "{ pythonRuns { id flow { id } } }")
    assert not listed.errors, listed.errors
    assert listed.data is not None
    assert listed.data["pythonRuns"] == [
        {"id": str(run.pk), "flow": {"id": str(flow.pk)}}
    ]
    assert (
        await _run(
            by_run, "query ($id: ID!) { pythonRun(id: $id) { id } }", id=str(other.pk)
        )
    ).errors


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_member_puts_a_run_in_and_it_brings_its_flow_and_workspace(
    authenticated_context: HttpContext, guest: GuestFactory, make_run: MakeRun
) -> None:
    run = await make_run()
    key = str(uuid.uuid4())  # lok's: nothing of it is here until something is put in

    added = await _run(
        authenticated_context,
        ADD,
        input={
            "collaboration": key,
            "identifier": "@fluss/run",
            "object": str(run.pk),
            "name": "Results",
        },
    )
    assert not added.errors, added.errors
    assert added.data is not None
    assert added.data["addToCollaboration"]["key"] == key
    assert added.data["addToCollaboration"]["name"] == "Results"
    items = {
        (item["identifier"], item["brought"])
        for item in added.data["addToCollaboration"]["items"]
    }
    assert items == {
        ("@fluss/run", False),
        ("@fluss/flow", True),
        ("@fluss/workspace", True),
    }

    shown = await _run(
        authenticated_context,
        "query ($key: ID!) { collaboration(key: $key) { key name itemCount(brought: false) } }",
        key=key,
    )
    assert data_of(shown)["collaboration"] == {
        "key": key,
        "name": "Results",
        "itemCount": 1,
    }

    ctx = guest({key: []})
    assert _ids(data_of(await _run(ctx, RUNS))["runs"]) == [str(run.pk)]
    listed = await _run(ctx, "{ collaborations { key } }")
    assert data_of(listed)["collaborations"] == [{"key": key}]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_guest_writes_nothing_even_as_an_editor(
    authenticated_context: HttpContext,
    guest: GuestFactory,
    make_run: MakeRun,
    make_workspace: MakeWorkspace,
) -> None:
    run = await make_run()
    python_flow = await _python_flow(authenticated_context, "Published")
    key = await _collaboration(authenticated_context, run, python_flow)
    ctx = guest({key: ["fluss_editor"]})

    _refused(
        await _run(
            ctx,
            CREATE_RUN,
            input={
                "flow": str(run.flow_id),
                "taskId": "guest-task",
                "snapshotInterval": 5,
            },
        ),
        "SCOPED_READ_ONLY",
    )
    _refused(
        await _run(
            ctx,
            TRACK,
            input={
                "run": str(run.pk),
                "reference": "ref-1",
                "t": 1,
                "kind": "NEXT",
                "causedBy": [],
                "source": "node-1",
                "handle": "out-0",
            },
        ),
        "SCOPED_READ_ONLY",
    )
    _refused(
        await _run(
            ctx,
            CREATE_PYTHON_RUN,
            input={"flow": str(python_flow.pk), "taskId": "guest-task"},
        ),
        "SCOPED_READ_ONLY",
    )
    workspace = await sync_to_async(lambda: run.flow.workspace)()
    _refused(
        await _run(
            ctx,
            UPDATE_WORKSPACE,
            input={
                "workspace": str(workspace.id),
                "graph": {"nodes": [], "edges": [], "globals": []},
            },
        ),
        "SCOPED_READ_ONLY",
    )
    elsewhere = await make_workspace(title="Elsewhere")
    _refused(
        await _run(
            ctx,
            ADD,
            input={
                "collaboration": key,
                "identifier": "@fluss/workspace",
                "object": str(elsewhere.pk),
            },
        ),
        "SCOPED_READ_ONLY",
    )

    assert await models.Run.objects.acount() == 1
    assert await models.RunEvent.objects.acount() == 0
    assert await models.PythonRun.objects.acount() == 0
    collaboration = await Collaboration.objects.aget(key=key)
    assert (
        await sync_to_async(collaboration.items.count)() == 4
    )  # the run, its flow and workspace, the Python flow


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_root_fields_handing_out_no_objects_are_closed_to_guests(
    authenticated_context: HttpContext,
    guest: GuestFactory,
    make_workspace: MakeWorkspace,
) -> None:
    ctx = guest(
        {await _collaboration(authenticated_context, await make_workspace()): []}
    )
    _refused(
        await _run(ctx, "{ workspaceStats { count } }"), "COLLABORATION_DOES_NOT_REACH"
    )
    # Validating a source reads the organization's actions: nothing a collaboration holds.
    _refused(
        await _run(
            ctx, '{ validatePythonFlow(input: {source: "def main(): pass"}) { ok } }'
        ),
        "COLLABORATION_DOES_NOT_REACH",
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_collaboration_of_another_organization_shows_nothing(
    other_org_context: HttpContext, guest: GuestFactory, make_workspace: MakeWorkspace
) -> None:
    theirs = await make_workspace(context=other_org_context, title="Theirs")
    ctx = guest({await _collaboration(other_org_context, theirs): []})

    assert data_of(await _run(ctx, WORKSPACES))["workspaces"] == []
    assert (await _run(ctx, WORKSPACE, id=str(theirs.pk))).errors


def _type_line(sdl: str, name: str) -> str:
    return next(line for line in sdl.splitlines() if line.startswith(f"type {name} "))


def test_the_schema_says_what_each_type_is() -> None:
    sdl = str(schema)
    assert '@identified(by: "@fluss/workspace")' in _type_line(sdl, "Workspace")
    assert '@identified(by: "@fluss/run")' in _type_line(sdl, "Run")

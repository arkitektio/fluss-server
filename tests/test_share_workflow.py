"""Sharing a workflow: what a root task created in fluss, put in a collaboration as it is now.

A workflow is a root task (koherent's ``Task.root_task_id``). What it made here is its runs: a run
records the task it was created through (``created_through``) from the provenance token the agent
sends with ``createRun`` / ``createPythonRun`` (the ``Rekuest-Task`` header, signed by the test rekuest
key in ``tests/fixtures/provenance_key.json``). Workspaces, flows and Python flows record no creating
task, and a workflow share says so (``unknown``).

The collaboration is lok's, named by a key: a full member shares under a fresh one, and a guest's
token names the same key.
"""

import datetime
import json
import pathlib
import uuid
from dataclasses import dataclass
from typing import Any

import pytest
from arkitekt_service.collaborations.models import Collaboration, CollaborationItem
from asgiref.sync import sync_to_async
from joserfc import jwt
from joserfc.jwk import OKPKey
from kante.context import HttpContext
from koherent.models import Task
from strawberry.types import ExecutionResult

from fluss_server.schema import schema
from reaktion import models
from tests.conftest import token_context
from tests.utils import GuestFactory, MakeFlow, data_of

#: A GraphQL payload, as strawberry hands it over.
GraphQLData = dict[str, Any]

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]

KEY = OKPKey.import_key(
    json.loads(
        (pathlib.Path(__file__).parent / "fixtures" / "provenance_key.json").read_text()
    )
)
#: Every workflow share reports these: nothing records which workflow made one of theirs.
UNKNOWN = ["@fluss/workspace", "@fluss/flow", "@fluss/pythonflow"]

CREATE_RUN = """
mutation ($input: CreateRunInput!) {
  createRun(input: $input) { id taskId }
}
"""
CREATE_PYTHON_RUN = """
mutation ($input: CreatePythonRunInput!) {
  createPythonRun(input: $input) { id taskId }
}
"""
TRACK = "mutation ($input: TrackInput!) { track(input: $input) { id } }"
SNAPSHOT = "mutation ($input: SnapshotRunInput!) { snapshot(input: $input) { id } }"
SHARE = """
mutation ($input: ShareWorkflowInput!) {
  shareWorkflow(input: $input) {
    collaboration
    dryRun
    added { identifier object }
    covered
    skipped { identifier object wholeIdentifier whole }
    unknown
  }
}
"""
LISTS = """
query ($runs: RunFilter, $pythonRuns: PythonRunFilter, $flows: FlowFilter, $workspaces: WorkspaceFilter) {
  runs(filters: $runs) { id }
  pythonRuns(filters: $pythonRuns) { id }
  flows(filters: $flows) { id }
  workspaces(filters: $workspaces) { id }
}
"""
RENDER_RUN = """
query ($id: ID!) {
  run(id: $id) {
    id
    flow { id }
    events { id }
    snapshots { id }
  }
}
"""


def task_token(task: str, root: str) -> str:
    """A task token as rekuest signs it for the static test app (user "1", client "static"):
    the task ``task`` of the workflow ``root``."""
    now = int(datetime.datetime.now(datetime.UTC).timestamp())
    return jwt.encode(
        {"alg": "Ed25519", "kid": "fluss-test-provenance"},
        {
            "iss": "rekuest",
            "aud": ["fluss"],
            "sub": "1",
            "act": {"sub": "1", "cid": "static", "iss": "static_issuer"},
            "iat": now,
            "exp": now + 300,
            "jti": uuid.uuid4().hex,
            "tsk": task,
            "ptk": root if task != root else None,
            "rtk": root,
            "rcb": "1",
            "ahs": "e3b0c44298fc1c14",
            "aha": "sha256-canonical-v1",
        },
        KEY,
        algorithms=["Ed25519"],
    )


async def _run(ctx: HttpContext, query: str, **variables: object) -> ExecutionResult:
    return await schema.execute(
        query, context_value=ctx, variable_values=variables or None
    )


async def _member(
    query: str, task: str | None = None, **variables: object
) -> GraphQLData:
    """Run ``query`` as the full member, as a request of its own (under the task token ``task``)."""
    return data_of(await _run(token_context("test", task=task), query, **variables))


@sync_to_async
def _published_python_flow(ctx: HttpContext) -> models.PythonFlow:
    return models.PythonFlow.objects.create(
        organization=ctx.request.organization,
        creator=ctx.request.user,
        title="Published",
        source="async def main() -> None:\n    return None\n",
        runtime="test",
        status="PUBLISHED",
        hash=uuid.uuid4().hex,
    )


async def _create_run(flow: models.Flow, task: str, token: str | None) -> models.Run:
    made = await _member(
        CREATE_RUN,
        task=token,
        input={"flow": str(flow.pk), "taskId": task, "snapshotInterval": 5},
    )
    return await models.Run.objects.select_related("created_through").aget(
        pk=made["createRun"]["id"]
    )


async def _create_python_run(
    flow: models.PythonFlow, task: str, token: str | None
) -> models.PythonRun:
    made = await _member(
        CREATE_PYTHON_RUN, task=token, input={"flow": str(flow.pk), "taskId": task}
    )
    return await models.PythonRun.objects.select_related("created_through").aget(
        pk=made["createPythonRun"]["id"]
    )


@dataclass(frozen=True)
class Workflow:
    """A workflow's root task and the runs it created, beside what it did not create."""

    root: str
    #: The flow its run executes (its id).
    flow: str
    run: models.Run
    python_run: models.PythonRun
    event: str
    snapshot: str
    #: Created without a provenance token, on the same flow.
    unrecorded: models.Run
    #: Created by another workflow.
    elsewhere: models.Run


async def _workflow(ctx: HttpContext, make_flow: MakeFlow) -> Workflow:
    """A workflow (two tasks under one root) that ran a flow (tracking an event and a snapshot) and
    a Python flow; plus a run made without a token and one made by another workflow."""
    flow = await make_flow(title="Graph")
    python_flow = await _published_python_flow(ctx)
    root = f"root-{uuid.uuid4().hex}"
    first, second = f"task-{uuid.uuid4().hex}", f"task-{uuid.uuid4().hex}"

    run = await _create_run(flow, first, task_token(first, root))
    event = (
        await _member(
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
    )["track"]["id"]
    snapshot = (
        await _member(SNAPSHOT, input={"run": str(run.pk), "events": [event], "t": 1})
    )["snapshot"]["id"]
    python_run = await _create_python_run(python_flow, second, task_token(second, root))

    unrecorded = await _create_run(flow, f"task-{uuid.uuid4().hex}", None)
    other = f"task-{uuid.uuid4().hex}"
    elsewhere = await _create_run(
        flow, other, task_token(other, f"root-{uuid.uuid4().hex}")
    )
    return Workflow(
        root=root,
        flow=str(flow.pk),
        run=run,
        python_run=python_run,
        event=event,
        snapshot=snapshot,
        unrecorded=unrecorded,
        elsewhere=elsewhere,
    )


def _ids(data: GraphQLData, field: str) -> set[str]:
    return {row["id"] for row in data[field]}


def _report(workflow: Workflow, key: str, *, dry_run: bool) -> GraphQLData:
    """What sharing ``workflow`` reports: its two runs put in, nothing covered or left out."""
    return {
        "collaboration": key,
        "dryRun": dry_run,
        "added": [
            {"identifier": "@fluss/pythonrun", "object": str(workflow.python_run.pk)},
            {"identifier": "@fluss/run", "object": str(workflow.run.pk)},
        ],
        "covered": 0,
        "skipped": [],
        "unknown": UNKNOWN,
    }


def _sorted(share: GraphQLData) -> GraphQLData:
    return {
        **share,
        "added": sorted(share["added"], key=lambda a: (a["identifier"], a["object"])),
        "unknown": sorted(share["unknown"], key=UNKNOWN.index),
    }


async def test_a_run_records_the_task_it_was_created_through(
    authenticated_context: HttpContext, make_flow: MakeFlow
) -> None:
    workflow = await _workflow(authenticated_context, make_flow)

    assert workflow.run.created_through is not None
    assert workflow.run.created_through.task_id == workflow.run.task_id
    assert workflow.run.created_through.root_task_id == workflow.root
    assert await Task.objects.filter(
        pk=workflow.run.created_through.pk,
        organization=authenticated_context.request.organization,
    ).aexists(), "the task is the organization's the request acts in"
    assert workflow.python_run.created_through is not None
    assert workflow.python_run.created_through.task_id == workflow.python_run.task_id
    assert workflow.python_run.created_through.root_task_id == workflow.root
    assert workflow.unrecorded.created_through is None, "no token, no task"
    assert await Task.objects.acount() == 3, "one per task that created a run"


async def test_a_resumed_task_keeps_the_task_its_run_was_created_through(
    authenticated_context: HttpContext, make_flow: MakeFlow
) -> None:
    flow = await make_flow()
    task = f"task-{uuid.uuid4().hex}"
    created = await _create_run(flow, task, task_token(task, task))

    resumed = await _create_run(flow, task, None)

    assert resumed.pk == created.pk
    assert created.created_through is not None
    assert resumed.created_through == created.created_through


async def test_a_run_of_another_task_than_the_requests_is_refused(
    authenticated_context: HttpContext, make_flow: MakeFlow
) -> None:
    flow = await make_flow()
    python_flow = await _published_python_flow(authenticated_context)
    token = task_token("task-mine", "root-mine")

    graph = await _run(
        token_context("test", task=token),
        CREATE_RUN,
        input={"flow": str(flow.pk), "taskId": "task-other", "snapshotInterval": 5},
    )
    python = await _run(
        token_context("test", task=token),
        CREATE_PYTHON_RUN,
        input={"flow": str(python_flow.pk), "taskId": "task-other"},
    )

    for refused in (graph, python):
        assert refused.errors, "it was let through"
        assert "task-mine" in refused.errors[0].message, refused.errors
    assert await models.Run.objects.acount() == 0
    assert await models.PythonRun.objects.acount() == 0
    assert await Task.objects.acount() == 0, "a refusal records no task"


async def test_a_dry_run_says_what_sharing_a_workflow_puts_in_and_writes_nothing(
    authenticated_context: HttpContext, make_flow: MakeFlow
) -> None:
    workflow = await _workflow(authenticated_context, make_flow)
    key = str(uuid.uuid4())

    tried = await _member(
        SHARE, input={"collaboration": key, "rootTask": workflow.root, "dryRun": True}
    )

    assert _sorted(tried["shareWorkflow"]) == _report(workflow, key, dry_run=True)
    assert not await Collaboration.objects.filter(key=key).aexists(), (
        "a dry run makes no row of the collaboration here"
    )
    assert await CollaborationItem.objects.acount() == 0


async def test_sharing_a_workflow_puts_in_its_runs_and_a_guest_sees_exactly_that(
    authenticated_context: HttpContext, guest: GuestFactory, make_flow: MakeFlow
) -> None:
    workflow = await _workflow(authenticated_context, make_flow)
    key = str(uuid.uuid4())
    before = data_of(await _run(guest({key: []}), LISTS))
    assert all(rows == [] for rows in before.values()), (
        "a key granted before anything is put in here holds nothing"
    )

    shared = await _member(
        SHARE,
        input={"collaboration": key, "rootTask": workflow.root, "name": "Pilot"},
    )

    assert _sorted(shared["shareWorkflow"]) == _report(workflow, key, dry_run=False)
    collaboration = await Collaboration.objects.aget(key=key)
    assert collaboration.name == "Pilot"
    seen = data_of(await _run(guest({key: []}), LISTS))
    assert _ids(seen, "runs") == {str(workflow.run.pk)}, (
        "not the run made without a token, nor another workflow's"
    )
    assert _ids(seen, "pythonRuns") == {str(workflow.python_run.pk)}
    assert _ids(seen, "flows") == {str(workflow.flow)}, (
        "the flow the run executes came along"
    )
    rendered = data_of(
        await _run(guest({key: []}), RENDER_RUN, id=str(workflow.run.pk))
    )["run"]
    assert rendered["events"] == [{"id": workflow.event}]
    assert rendered["snapshots"] == [{"id": workflow.snapshot}], (
        "a run's events and snapshots are part of it"
    )
    for other in (workflow.unrecorded, workflow.elsewhere):
        assert (await _run(guest({key: []}), RENDER_RUN, id=str(other.pk))).errors

    stranger = data_of(await _run(guest({str(uuid.uuid4()): []}), LISTS))
    assert all(rows == [] for rows in stranger.values()), (
        "another key sees nothing of it"
    )


async def test_lists_filter_by_the_workflow_that_made_them_and_by_collaboration(
    authenticated_context: HttpContext, make_flow: MakeFlow
) -> None:
    workflow = await _workflow(authenticated_context, make_flow)
    key = str(uuid.uuid4())
    under = {"createdUnder": workflow.root}

    made = await _member(
        LISTS, runs=under, pythonRuns=under, flows=under, workspaces=under
    )

    assert _ids(made, "runs") == {str(workflow.run.pk)}
    assert _ids(made, "pythonRuns") == {str(workflow.python_run.pk)}
    assert made["flows"] == [] and made["workspaces"] == [], (
        "a flow and a workspace cannot say what made them"
    )

    inside = {"inCollaboration": key}
    nothing_yet = await _member(LISTS, runs=inside, pythonRuns=inside, flows=inside)
    assert all(nothing_yet[f] == [] for f in ("runs", "pythonRuns", "flows"))

    await _member(SHARE, input={"collaboration": key, "rootTask": workflow.root})
    shared = await _member(
        LISTS, runs=inside, pythonRuns=inside, flows=inside, workspaces=inside
    )

    assert _ids(shared, "runs") == {str(workflow.run.pk)}
    assert _ids(shared, "pythonRuns") == {str(workflow.python_run.pk)}
    assert _ids(shared, "flows") == {str(workflow.flow)}
    both = await _member(
        LISTS,
        runs={"createdUnder": workflow.root, "inCollaboration": key},
        flows={"inCollaboration": key, "ids": [str(workflow.flow)]},
        pythonRuns={"inCollaboration": key, "createdUnder": "root-nothing"},
    )
    assert _ids(both, "runs") == {str(workflow.run.pk)}
    assert _ids(both, "flows") == {str(workflow.flow)}
    assert both["pythonRuns"] == []


async def test_another_organization_shares_nothing_of_this_workflow(
    authenticated_context: HttpContext, make_flow: MakeFlow
) -> None:
    workflow = await _workflow(authenticated_context, make_flow)

    tried = data_of(
        await _run(
            token_context("othertest"),
            SHARE,
            input={
                "collaboration": str(uuid.uuid4()),
                "rootTask": workflow.root,
                "dryRun": True,
            },
        )
    )

    assert tried["shareWorkflow"]["added"] == []
    assert tried["shareWorkflow"]["skipped"] == []


async def test_an_explicit_null_filters_nothing(
    authenticated_context: HttpContext, make_flow: MakeFlow
) -> None:
    workflow = await _workflow(authenticated_context, make_flow)
    unset = {"inCollaboration": None, "createdUnder": None}

    listed = await _member(LISTS, runs=unset, pythonRuns=unset)

    assert _ids(listed, "runs") == {
        str(workflow.run.pk),
        str(workflow.unrecorded.pk),
        str(workflow.elsewhere.pk),
    }
    assert _ids(listed, "pythonRuns") == {str(workflow.python_run.pk)}

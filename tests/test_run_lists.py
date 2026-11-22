"""Lists the client used to narrow by itself, answered by the server.

- ``runs(filters: { status })``: the running runs, however old, not "running among the newest 30".
- ``creator`` (a lok sub) on workspaces, flows and Python flows: a member's work.
- ``pythonFlows(filters: { latest })``: one row per flow, its newest version.
- ``runs`` / ``run`` / ``pythonRuns`` / ``pythonRun`` subscriptions: a run's status heard, not polled.
"""

import asyncio
import hashlib
import uuid

import pytest
from asgiref.sync import sync_to_async

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


RUNS = """
query ($filters: RunFilter, $pagination: OffsetPaginationInput) {
  runs(filters: $filters, pagination: $pagination, ordering: [{ createdAt: DESC }]) { id status }
}
"""

WORKSPACES = """
query ($filters: WorkspaceFilter) { workspaces(filters: $filters) { id title } }
"""

FLOWS = """
query ($filters: FlowFilter) { flows(filters: $filters) { id title } }
"""

PYTHON_FLOWS = """
query ($filters: PythonFlowFilter) {
  pythonFlows(filters: $filters, ordering: [{ createdAt: ASC }]) { id title status }
}
"""


@sync_to_async
def _close(run) -> None:
    run.status = "COMPLETED"
    run.save()


async def test_running_runs_are_found_past_the_newest_page(aexecute, make_run):
    old_running = await make_run()
    for _ in range(3):
        await _close(await make_run())

    # The newest page holds only completed runs; the status filter still finds the old one.
    newest = await aexecute(RUNS, {"pagination": {"limit": 3}})
    assert not newest.errors, newest.errors
    assert all(run["status"] == "COMPLETED" for run in newest.data["runs"])

    running = await aexecute(RUNS, {"filters": {"status": ["RUNNING"]}, "pagination": {"limit": 3}})
    assert not running.errors, running.errors
    assert running.data["runs"] == [{"id": str(old_running.id), "status": "RUNNING"}]

    completed = await aexecute(RUNS, {"filters": {"status": ["COMPLETED"]}})
    assert not completed.errors, completed.errors
    assert len(completed.data["runs"]) == 3


@sync_to_async
def _other_member(context):
    """A second member of the same organization, with their own sub."""
    from authentikate.models import Membership, User

    user, _ = User.objects.get_or_create(sub="42", iss="static_issuer", defaults={"username": "static_issuer_42"})
    Membership.objects.get_or_create(user=user, organization=context.request.organization)
    return user


@sync_to_async
def _reassign(row, user) -> None:
    row.creator = user
    row.save()


async def test_creator_filters_by_the_members_sub(aexecute, authenticated_context, make_workspace, make_flow):
    mine = await make_workspace(title="Mine")
    theirs = await make_workspace(title="Theirs")
    other = await _other_member(authenticated_context)
    await _reassign(theirs, other)

    res = await aexecute(WORKSPACES, {"filters": {"creator": "42"}})
    assert not res.errors, res.errors
    assert res.data["workspaces"] == [{"id": str(theirs.id), "title": "Theirs"}]

    res = await aexecute(WORKSPACES, {"filters": {"creator": "1", "ids": [str(mine.id), str(theirs.id)]}})
    assert not res.errors, res.errors
    assert res.data["workspaces"] == [{"id": str(mine.id), "title": "Mine"}]

    flow = await make_flow(title="Their flow")
    await _reassign(flow, other)
    await make_flow(title="My flow")
    res = await aexecute(FLOWS, {"filters": {"creator": "42"}})
    assert not res.errors, res.errors
    assert res.data["flows"] == [{"id": str(flow.id), "title": "Their flow"}]


@sync_to_async
def _python_flow(context, title: str, lineage: uuid.UUID | None = None, previous=None, status: str = "DRAFT", creator=None):
    from reaktion.models import PythonFlow

    source = f"async def main() -> int:\n    return {uuid.uuid4().int % 1000}\n"
    return PythonFlow.objects.create(
        organization=context.request.organization,
        creator=creator or context.request.user,
        title=title,
        lineage=lineage or uuid.uuid4(),
        previous=previous,
        source=source,
        runtime="test",
        status=status,
        hash=hashlib.sha256(source.encode()).hexdigest(),
    )


async def test_latest_lists_each_flow_once_by_its_newest_version(aexecute, authenticated_context):
    first = await _python_flow(authenticated_context, "Segment v1", status="PUBLISHED")
    second = await _python_flow(authenticated_context, "Segment v2", lineage=first.lineage, previous=first, status="DRAFT")
    other = await _python_flow(authenticated_context, "Track", status="PUBLISHED")

    res = await aexecute(PYTHON_FLOWS, {"filters": {"latest": True}})
    assert not res.errors, res.errors
    assert [flow["id"] for flow in res.data["pythonFlows"]] == [str(second.id), str(other.id)]

    res = await aexecute(PYTHON_FLOWS, {"filters": {"latest": False}})
    assert not res.errors, res.errors
    assert [flow["id"] for flow in res.data["pythonFlows"]] == [str(first.id)]

    # The status applies to each flow's head: Segment's head is a draft, so a list of
    # published flows shows Track alone, not Segment's older published version.
    res = await aexecute(PYTHON_FLOWS, {"filters": {"latest": True, "status": ["PUBLISHED"]}})
    assert not res.errors, res.errors
    assert [flow["id"] for flow in res.data["pythonFlows"]] == [str(other.id)]

    other_member = await _other_member(authenticated_context)
    mine = await _python_flow(authenticated_context, "Theirs", creator=other_member)
    res = await aexecute(PYTHON_FLOWS, {"filters": {"latest": True, "creator": "42"}})
    assert not res.errors, res.errors
    assert [flow["id"] for flow in res.data["pythonFlows"]] == [str(mine.id)]


# --- subscriptions -------------------------------------------------------------------------


async def _heard(stream) -> list[dict]:
    return [message async for message in stream]


async def test_runs_are_heard_starting_and_completing_by_their_organization_alone(make_flow):
    from kante.testing import GraphQLWebSocketTestClient
    from reaktion.models import Run

    from fluss_server.asgi import application

    flow = await make_flow()
    watch = "subscription { runs { create { id status } update { id status } delete } }"

    async with (
        GraphQLWebSocketTestClient(application, connection_params={"token": "test"}) as member,
        GraphQLWebSocketTestClient(application, connection_params={"token": "othertest"}) as stranger,
    ):
        heard = asyncio.ensure_future(_heard(member.subscribe(watch, timeout=3, max_messages=2)))
        overheard = asyncio.ensure_future(_heard(stranger.subscribe(watch, timeout=2)))
        await asyncio.sleep(0.3)

        run = await sync_to_async(Run.objects.create)(flow=flow, task_id="t-1")
        await _close(run)

        messages = [message["payload"]["data"]["runs"] for message in await heard]
        assert messages == [
            {"create": {"id": str(run.id), "status": "RUNNING"}, "update": None, "delete": None},
            {"create": None, "update": {"id": str(run.id), "status": "COMPLETED"}, "delete": None},
        ]
        assert not any((message["payload"].get("data") or {}).get("runs") for message in await overheard)


async def test_one_run_is_heard_and_another_is_not(make_run):
    from kante.testing import GraphQLWebSocketTestClient

    from fluss_server.asgi import application

    watched = await make_run()
    watched_id = str(watched.id)
    other = await make_run()
    watch = f'subscription {{ run(id: "{watched.id}") {{ update {{ id status }} delete }} }}'

    async with GraphQLWebSocketTestClient(application, connection_params={"token": "test"}) as member:
        heard = asyncio.ensure_future(_heard(member.subscribe(watch, timeout=2)))
        await asyncio.sleep(0.3)

        await _close(other)
        await _close(watched)
        await sync_to_async(watched.delete)()

        messages = [message["payload"]["data"]["run"] for message in await heard]
        assert messages == [
            {"update": {"id": watched_id, "status": "COMPLETED"}, "delete": None},
            {"update": None, "delete": watched_id},
        ]


async def test_a_run_of_another_organization_cannot_be_watched(make_run):
    from kante.testing import GraphQLWebSocketTestClient

    from fluss_server.asgi import application

    run = await make_run()
    watch = f'subscription {{ run(id: "{run.id}") {{ update {{ id }} }} }}'
    async with GraphQLWebSocketTestClient(application, connection_params={"token": "othertest"}) as stranger:
        messages = await _heard(stranger.subscribe(watch, timeout=2))
    assert messages, "the refusal is answered"
    assert all(not (message["payload"].get("data") or {}).get("run") for message in messages)


async def test_python_runs_are_heard_finishing(authenticated_context):
    from django.utils import timezone
    from kante.testing import GraphQLWebSocketTestClient
    from reaktion.models import PythonRun

    from fluss_server.asgi import application

    flow = await _python_flow(authenticated_context, "Segment", status="PUBLISHED")
    run = await sync_to_async(PythonRun.objects.create)(flow=flow, task_id="t-1")

    list_watch = "subscription { pythonRuns { update { id status } } }"
    one_watch = f'subscription {{ pythonRun(id: "{run.id}") {{ update {{ id status finishedAt }} }} }}'

    async with (
        GraphQLWebSocketTestClient(application, connection_params={"token": "test"}) as member,
        GraphQLWebSocketTestClient(application, connection_params={"token": "test"}) as page,
        GraphQLWebSocketTestClient(application, connection_params={"token": "othertest"}) as stranger,
    ):
        listed = asyncio.ensure_future(anext(member.subscribe(list_watch, timeout=3, max_messages=1)))
        one = asyncio.ensure_future(anext(page.subscribe(one_watch, timeout=3, max_messages=1)))
        overheard = asyncio.ensure_future(_heard(stranger.subscribe(list_watch, timeout=2)))
        await asyncio.sleep(0.3)

        run.status = "FAILED"
        run.finished_at = timezone.now()
        await sync_to_async(run.save)()

        assert (await listed)["payload"]["data"]["pythonRuns"] == {"update": {"id": str(run.id), "status": "FAILED"}}
        heard = (await one)["payload"]["data"]["pythonRun"]["update"]
        assert heard["id"] == str(run.id) and heard["status"] == "FAILED" and heard["finishedAt"]
        assert not any((message["payload"].get("data") or {}).get("pythonRuns") for message in await overheard)

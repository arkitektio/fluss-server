"""PythonFlow versions and runs, executed against the schema on a real Postgres."""

import pytest

from reaktion.models import PythonFlow, PythonRun

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


CREATE = """
mutation ($input: CreatePythonFlowInput!) {
  createPythonFlow(input: $input) {
    id title status hash lineage physical
    previous { id }
    args { key kind }
    returns { key kind }
    manifest { alias actionHash effect }
  }
}
"""
UPDATE = """
mutation ($input: UpdatePythonFlowInput!) { updatePythonFlow(input: $input) { id title description } }
"""
PUBLISH = """
mutation ($input: PythonFlowRefInput!) { publishPythonFlow(input: $input) { id status } }
"""
ARCHIVE = """
mutation ($input: PythonFlowRefInput!) { archivePythonFlow(input: $input) { id status } }
"""
DELETE = """
mutation ($input: PythonFlowRefInput!) { deletePythonFlow(input: $input) }
"""
CREATE_RUN = """
mutation ($input: CreatePythonRunInput!) { createPythonRun(input: $input) { id status taskId flow { id } } }
"""
CLOSE_RUN = """
mutation ($input: ClosePythonRunInput!) { closePythonRun(input: $input) { id status finishedAt } }
"""
GET = """
query ($id: ID!) { pythonFlow(id: $id) { id versions { id } } }
"""
LIST = """
query ($filters: PythonFlowFilter) { pythonFlows(filters: $filters) { id status } }
"""

SOURCE = "def main(x: int) -> int:\n    return segment(x)\n"


def _input(source: str = SOURCE, **overrides) -> dict:
    return {
        "source": source,
        "title": "Segment",
        "args": [{"key": "x", "kind": "INT", "nullable": False}],
        "returns": [{"key": "return0", "kind": "INT", "nullable": False}],
        "manifest": [{"alias": "segment", "actionHash": "abc123", "effect": "NONE"}],
        "runtime": "monty-0.1/helpers-1",
        **overrides,
    }


async def _create(aexecute, context=None, **overrides) -> dict:
    res = await aexecute(CREATE, {"input": _input(**overrides)}, context=context)
    assert not res.errors, res.errors
    return res.data["createPythonFlow"]


async def _published(aexecute, **overrides) -> dict:
    flow = await _create(aexecute, **overrides)
    res = await aexecute(PUBLISH, {"input": {"id": flow["id"]}})
    assert not res.errors, res.errors
    return flow


# --- versions ----------------------------------------------------------------------------


async def test_create_stores_a_draft_with_typed_ports(aexecute, authenticated_context):
    flow = await _create(aexecute)
    assert flow["status"] == "DRAFT"
    assert flow["args"] == [{"key": "x", "kind": "INT"}]
    assert flow["manifest"] == [{"alias": "segment", "actionHash": "abc123", "effect": "NONE"}]
    assert flow["physical"] is False
    row = await PythonFlow.objects.aget(id=flow["id"])
    assert row.organization_id == authenticated_context.request.organization.id


async def test_identical_content_in_a_lineage_is_the_same_version(aexecute):
    first = await _create(aexecute)
    again = await _create(aexecute, previous=first["id"], title="Renamed only")
    assert again["id"] == first["id"]
    assert await PythonFlow.objects.acount() == 1


async def test_changed_source_is_a_new_version_in_the_same_lineage(aexecute):
    first = await _create(aexecute)
    second = await _create(aexecute, source=SOURCE + "# tweak\n", previous=first["id"])
    assert second["id"] != first["id"]
    assert second["lineage"] == first["lineage"]
    assert second["previous"] == {"id": first["id"]}
    assert second["title"] == "Segment"

    res = await aexecute(GET, {"id": first["id"]})
    assert not res.errors, res.errors
    assert [v["id"] for v in res.data["pythonFlow"]["versions"]] == [first["id"], second["id"]]


async def test_same_content_without_previous_starts_a_new_lineage(aexecute):
    first = await _create(aexecute)
    other = await _create(aexecute)
    assert other["id"] != first["id"]
    assert other["lineage"] != first["lineage"]


async def test_title_and_description_change_in_place(aexecute):
    flow = await _create(aexecute)
    res = await aexecute(UPDATE, {"input": {"id": flow["id"], "title": "Better", "description": "What it does"}})
    assert not res.errors, res.errors
    assert res.data["updatePythonFlow"] == {"id": flow["id"], "title": "Better", "description": "What it does"}
    assert (await PythonFlow.objects.aget(id=flow["id"])).hash == flow["hash"]


async def test_a_physical_action_marks_the_flow_physical(aexecute):
    flow = await _create(aexecute, manifest=[{"alias": "move_stage", "actionHash": "h", "effect": "PHYSICAL"}])
    assert flow["physical"] is True


# --- validation --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"manifest": [{"alias": "segment", "actionHash": "a"}, {"alias": "segment", "actionHash": "b"}]}, "unique"),
        ({"manifest": [{"alias": "not an identifier", "actionHash": "a"}]}, "identifier"),
        ({"manifest": [{"alias": "lambda", "actionHash": "a"}]}, "identifier"),
        ({"entrypoint": "main()"}, "identifier"),
        ({"args": [{"key": "xs", "kind": "LIST", "nullable": False}]}, "exactly one child"),
    ],
)
async def test_a_malformed_report_is_rejected(aexecute, overrides, message):
    res = await aexecute(CREATE, {"input": _input(**overrides)})
    assert res.errors and message in res.errors[0].message
    assert not await PythonFlow.objects.aexists()


# --- lifecycle ---------------------------------------------------------------------------


async def test_publish_then_archive(aexecute):
    flow = await _published(aexecute)
    assert (await PythonFlow.objects.aget(id=flow["id"])).status == "PUBLISHED"
    res = await aexecute(ARCHIVE, {"input": {"id": flow["id"]}})
    assert not res.errors, res.errors
    assert res.data["archivePythonFlow"]["status"] == "ARCHIVED"


@pytest.mark.parametrize(
    "publish_first, mutation",
    [(True, PUBLISH), (False, ARCHIVE), (True, DELETE)],
    ids=["publish-twice", "archive-a-draft", "delete-published"],
)
async def test_the_lifecycle_only_moves_forward(aexecute, publish_first, mutation):
    flow = await (_published(aexecute) if publish_first else _create(aexecute))
    res = await aexecute(mutation, {"input": {"id": flow["id"]}})
    assert res.errors and "PythonFlow" in res.errors[0].message


async def test_reverting_to_archived_content_republishes_that_version(aexecute):
    v1 = await _published(aexecute)
    res = await aexecute(ARCHIVE, {"input": {"id": v1["id"]}})
    assert not res.errors, res.errors
    v2 = await _published(aexecute, source=SOURCE + "# v2\n", previous=v1["id"])

    back = await _create(aexecute, previous=v2["id"])
    assert back["id"] == v1["id"]
    res = await aexecute(PUBLISH, {"input": {"id": back["id"]}})
    assert not res.errors, res.errors
    assert res.data["publishPythonFlow"]["status"] == "PUBLISHED"


async def test_deleting_the_organization_or_creator_is_not_blocked_by_runs(aexecute, authenticated_context):
    flow = await _published(aexecute)
    res = await aexecute(CREATE_RUN, {"input": {"flow": flow["id"], "taskId": "task-1"}})
    assert not res.errors, res.errors

    await authenticated_context.request.user.adelete()
    row = await PythonFlow.objects.aget(id=flow["id"])
    assert row.creator_id is None
    await authenticated_context.request.organization.adelete()
    assert not await PythonFlow.objects.aexists()
    assert not await PythonRun.objects.aexists()


async def test_a_draft_can_be_deleted(aexecute):
    flow = await _create(aexecute)
    res = await aexecute(DELETE, {"input": {"id": flow["id"]}})
    assert not res.errors, res.errors
    assert not await PythonFlow.objects.filter(id=flow["id"]).aexists()


async def test_list_filters_by_status(aexecute):
    draft = await _create(aexecute)
    published = await _published(aexecute, source=SOURCE + "# v2\n")
    res = await aexecute(LIST, {"filters": {"status": ["PUBLISHED"]}})
    assert not res.errors, res.errors
    assert [f["id"] for f in res.data["pythonFlows"]] == [published["id"]]
    assert draft["id"] not in [f["id"] for f in res.data["pythonFlows"]]


# --- runs --------------------------------------------------------------------------------


async def test_a_run_of_a_published_flow(aexecute):
    flow = await _published(aexecute)
    res = await aexecute(CREATE_RUN, {"input": {"flow": flow["id"], "taskId": "task-1"}})
    assert not res.errors, res.errors
    run = res.data["createPythonRun"]
    assert (run["status"], run["taskId"], run["flow"]["id"]) == ("RUNNING", "task-1", flow["id"])

    again = await aexecute(CREATE_RUN, {"input": {"flow": flow["id"], "taskId": "task-1"}})
    assert again.data["createPythonRun"]["id"] == run["id"]

    res = await aexecute(CLOSE_RUN, {"input": {"run": run["id"], "status": "FAILED"}})
    assert not res.errors, res.errors
    assert res.data["closePythonRun"]["status"] == "FAILED"
    assert res.data["closePythonRun"]["finishedAt"]


async def test_a_draft_cannot_be_run(aexecute):
    flow = await _create(aexecute)
    res = await aexecute(CREATE_RUN, {"input": {"flow": flow["id"], "taskId": "task-1"}})
    assert res.errors and "PUBLISHED" in res.errors[0].message
    assert not await PythonRun.objects.aexists()


# --- organizations -----------------------------------------------------------------------


async def test_another_organization_cannot_see_or_touch_a_flow(aexecute, other_org_context):
    flow = await _published(aexecute)

    res = await aexecute(GET, {"id": flow["id"]}, context=other_org_context)
    assert res.errors
    res = await aexecute(LIST, {}, context=other_org_context)
    assert not res.errors, res.errors
    assert res.data["pythonFlows"] == []
    for mutation in (ARCHIVE, DELETE):
        res = await aexecute(mutation, {"input": {"id": flow["id"]}}, context=other_org_context)
        assert res.errors
    res = await aexecute(CREATE_RUN, {"input": {"flow": flow["id"], "taskId": "t"}}, context=other_org_context)
    assert res.errors
    # Nor can it chain a version onto it.
    res = await aexecute(CREATE, {"input": _input(previous=flow["id"])}, context=other_org_context)
    assert res.errors
    assert (await PythonFlow.objects.aget(id=flow["id"])).status == "PUBLISHED"

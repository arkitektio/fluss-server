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
RUN_FOR_TASK = """
query ($id: ID!) { pythonRunForTask(id: $id) { id flow { id } } }
"""
GET = """
query ($id: ID!) { pythonFlow(id: $id) { id versions { id } } }
"""
LIST = """
query ($filters: PythonFlowFilter) { pythonFlows(filters: $filters) { id status } }
"""

VALIDATE = """
query ($input: PythonFlowSourceInput!) {
  validatePythonFlow(input: $input) {
    ok stubs runtime
    diagnostics { message line }
    args { key kind nullable default }
    returns { key kind }
  }
}
"""

SOURCE = "async def main(x: int, times: int = 2) -> int:\n    return await segment(x)\n"


def _action(alias: str, action_hash: str, effect: str | None = None, **overrides) -> dict:
    """A manifest entry for an INT -> INT FUNCTION action, with its ports."""
    return {
        "alias": alias,
        "actionHash": action_hash,
        "kind": "FUNCTION",
        "args": [{"key": "x", "kind": "INT", "nullable": False}],
        "returns": [{"key": "return0", "kind": "INT", "nullable": False}],
        **({"effect": effect} if effect else {}),
        **overrides,
    }


def _input(source: str = SOURCE, **overrides) -> dict:
    return {"source": source, "title": "Segment", "manifest": [_action("segment", "abc123", "NONE")], **overrides}


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


async def test_create_stores_a_draft_with_the_ports_its_source_declares(aexecute, authenticated_context):
    flow = await _create(aexecute)
    assert flow["status"] == "DRAFT"
    assert flow["args"] == [{"key": "x", "kind": "INT"}, {"key": "times", "kind": "INT"}]
    assert flow["returns"] == [{"key": "return0", "kind": "INT"}]
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


async def test_an_irreversible_action_marks_the_flow_physical(aexecute):
    flow = await _create(aexecute, manifest=[_action("segment", "abc123"), _action("move_stage", "h", "IRREVERSIBLE")])
    assert flow["physical"] is True


async def test_an_undeclared_effect_is_unknown_and_not_physical(aexecute):
    flow = await _create(aexecute, manifest=[_action("segment", "h"), _action("snap", "g", "REPEATABLE")])
    assert [entry["effect"] for entry in flow["manifest"]] == ["UNKNOWN", "REPEATABLE"]
    assert flow["physical"] is False


# --- validation --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"manifest": [_action("segment", "a"), _action("segment", "b")]}, "unique"),
        ({"manifest": [_action("not an identifier", "a")]}, "identifier"),
        ({"manifest": [_action("lambda", "a")]}, "identifier"),
        ({"entrypoint": "main()"}, "identifier"),
        ({"manifest": [_action("segment", "a", args=[{"key": "xs", "kind": "LIST", "nullable": False}])]}, "exactly one child"),
    ],
)
async def test_a_malformed_input_is_rejected(aexecute, overrides, message):
    res = await aexecute(CREATE, {"input": _input(**overrides)})
    assert res.errors and message in res.errors[0].message
    assert not await PythonFlow.objects.aexists()


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"source": "async def main(x: int) -> int:\n    return await segment('no int')\n"}, "line 2"),
        ({"source": "async def main(x: int) -> int:\n    return await snap(x)\n"}, "snap"),
        ({"source": "def main(x: int) -> int:\n    return x\n"}, "async def"),
        ({"source": "async def main(x) -> int:\n    return x\n"}, "annotation"),
        ({"manifest": [_action("segment", "a", kind="GENERATOR")]}, "FUNCTION"),
    ],
    ids=["type-error", "outside-the-manifest", "not-async", "unannotated", "generator-action"],
)
async def test_a_source_that_does_not_validate_is_refused(aexecute, overrides, message):
    res = await aexecute(CREATE, {"input": _input(**overrides)})
    assert res.errors and "does not validate" in res.errors[0].message, res.errors
    assert message in res.errors[0].message, res.errors[0].message
    assert not await PythonFlow.objects.aexists()


async def test_the_ports_are_derived_never_taken_from_the_client(aexecute):
    res = await aexecute(CREATE, {"input": _input(args=[{"key": "y", "kind": "STRING", "nullable": False}])})
    assert res.errors and "args" in res.errors[0].message
    assert not await PythonFlow.objects.aexists()


async def test_a_new_signature_is_a_new_version(aexecute):
    first = await _create(aexecute)
    second = await _create(aexecute, source=SOURCE.replace("times: int = 2", "times: int = 3"), previous=first["id"])
    assert second["id"] != first["id"]


async def test_validating_a_source_stores_nothing_and_reports_its_ports_and_stubs(aexecute):
    res = await aexecute(VALIDATE, {"input": {"source": SOURCE, "manifest": [_action("segment", "abc123")]}})
    assert not res.errors, res.errors
    report = res.data["validatePythonFlow"]
    assert report["ok"] and report["diagnostics"] == []
    assert report["args"] == [{"key": "x", "kind": "INT", "nullable": False, "default": None}, {"key": "times", "kind": "INT", "nullable": False, "default": 2}]
    assert "async def segment(x: int) -> int: ..." in report["stubs"]
    assert report["runtime"].startswith("monty-")
    assert not await PythonFlow.objects.aexists()

    res = await aexecute(VALIDATE, {"input": {"source": SOURCE.replace("segment(x)", "segment('no')"), "manifest": [_action("segment", "abc123")]}})
    assert not res.errors, res.errors
    report = res.data["validatePythonFlow"]
    assert not report["ok"] and report["args"] == []
    assert "segment" in report["diagnostics"][0]["message"]


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


async def test_a_run_is_closed_once(aexecute):
    flow = await _published(aexecute)
    run = (await aexecute(CREATE_RUN, {"input": {"flow": flow["id"], "taskId": "task-1"}})).data["createPythonRun"]

    res = await aexecute(CLOSE_RUN, {"input": {"run": run["id"], "status": "CANCELLED"}})
    assert not res.errors, res.errors
    assert res.data["closePythonRun"]["status"] == "CANCELLED"

    again = await aexecute(CLOSE_RUN, {"input": {"run": run["id"], "status": "COMPLETED"}})
    assert again.errors and "RUNNING" in again.errors[0].message
    assert (await PythonRun.objects.aget(id=run["id"])).status == "CANCELLED"


async def test_a_resumed_task_reopens_its_closed_run(aexecute):
    """An agent that died after closing the run, before its task ended: the task runs again."""
    flow = await _published(aexecute)
    run = (await aexecute(CREATE_RUN, {"input": {"flow": flow["id"], "taskId": "task-1"}})).data["createPythonRun"]
    await aexecute(CLOSE_RUN, {"input": {"run": run["id"], "status": "COMPLETED"}})
    created_at = (await PythonRun.objects.aget(id=run["id"])).created_at

    res = await aexecute(CREATE_RUN, {"input": {"flow": flow["id"], "taskId": "task-1"}})
    assert not res.errors, res.errors
    assert (res.data["createPythonRun"]["id"], res.data["createPythonRun"]["status"]) == (run["id"], "RUNNING")
    reopened = await PythonRun.objects.aget(id=run["id"])
    assert (reopened.finished_at, reopened.created_at) == (None, created_at)


async def test_a_run_is_found_by_its_task(aexecute, other_org_context):
    flow = await _published(aexecute)
    run = (await aexecute(CREATE_RUN, {"input": {"flow": flow["id"], "taskId": "task-1"}})).data["createPythonRun"]

    res = await aexecute(RUN_FOR_TASK, {"id": "task-1"})
    assert not res.errors, res.errors
    assert (res.data["pythonRunForTask"]["id"], res.data["pythonRunForTask"]["flow"]["id"]) == (run["id"], flow["id"])

    assert (await aexecute(RUN_FOR_TASK, {"id": "task-2"})).errors
    assert (await aexecute(RUN_FOR_TASK, {"id": "task-1"}, context=other_org_context)).errors


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

"""``descriptors`` on fluss's types: what an object says about itself, from its structure's declaration.

One declaration (``fluss_server.service``) feeds the manifest, the signals and this field, so the
tests hold the three to each other: the field answers what a signal about the object carries, in
the keys the manifest declares. The descriptors are stored, so a port's ``requires`` is a filter
on the list query. And the agent's sweep, run for one organization, does only that
organization's share.
"""

import uuid

import pytest
from asgiref.sync import sync_to_async
from authentikate.models import Organization
from django.core.management import call_command

from embeddings import engine
from embeddings.healer import stale_queryset
from fluss_server.hook_agent import agent
from fluss_server.service import service
from reaktion.models import Flow, PythonFlow, PythonRun, Run, Workspace
from tests.test_signals import intake  # noqa: F401  the fixture

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]

DESCRIBED = """
    query Described($workspace: ID!, $flow: ID!, $run: ID!, $pythonFlow: ID!, $pythonRun: ID!) {
        workspace(id: $workspace) { descriptors }
        flow(id: $flow) { descriptors }
        run(id: $run) { descriptors }
        pythonFlow(id: $pythonFlow) { descriptors }
        pythonRun(id: $pythonRun) { descriptors }
        flows { id descriptors }
    }
"""


UPDATE_WORKSPACE = """
    mutation ($input: UpdateWorkspaceInput!) { updateWorkspace(input: $input) { id } }
"""


def _node(node_id: str, kind: str, ins: list, outs: list) -> dict:
    return {"id": node_id, "kind": kind, "position": {"x": 0, "y": 0}, "ins": ins, "outs": outs, "constants": [], "voids": [], "constantsMap": {}, "globalsMap": {}}


#: One argument, no return: a flow a batch runner can feed one list at a time.
IMAGES = {"key": "xs", "kind": "LIST", "nullable": False, "children": [{"key": "...", "kind": "STRUCTURE", "identifier": "@mikro/image", "nullable": False}]}
GRAPH = {"nodes": [_node("1", "ARGS", [[]], [[IMAGES]]), _node("2", "RETURNS", [[]], [[]])], "edges": [], "globals": []}


async def _seed(aexecute, ctx) -> dict:
    """One object of every structure fluss hosts, in the context's organization: the flow as the mutation saves it."""
    user, org = ctx.request.user, ctx.request.organization
    workspace = await Workspace.objects.acreate(title="Described", creator=user, organization=org)
    result = await aexecute(UPDATE_WORKSPACE, {"input": {"workspace": str(workspace.pk), "graph": GRAPH, "title": "Described flow"}})
    assert not result.errors, result.errors
    flow = await Flow.objects.aget(workspace=workspace, title="Described flow")

    @sync_to_async
    def rest() -> dict:
        run = Run.objects.create(flow=flow, task_id=uuid.uuid4().hex)
        python_flow = PythonFlow.objects.create(
            organization=org, creator=user, title="moves", source="def main(stage): pass", runtime="monty-0.1", hash=uuid.uuid4().hex, status="PUBLISHED",
            args=[{"key": "stage", "kind": "STRUCTURE", "identifier": "@mikro/stage", "nullable": False}],
            manifest=[{"alias": "move_stage", "action_hash": "a", "effect": "IRREVERSIBLE"}, {"alias": "snap", "action_hash": "b", "effect": "REPEATABLE"}],
        )
        python_run = PythonRun.objects.create(flow=python_flow, task_id=uuid.uuid4().hex)
        return {"workspace": workspace, "flow": flow, "run": run, "pythonFlow": python_flow, "pythonRun": python_run}

    return await rest()


async def test_an_object_answers_the_descriptors_its_structure_declares(aexecute, authenticated_context):
    seeded = await _seed(aexecute, authenticated_context)

    result = await aexecute(DESCRIBED, {name: str(obj.pk) for name, obj in seeded.items()})
    assert not result.errors, result.errors

    flow = {"@fluss/n_nodes": 2, "@fluss/n_edges": 0, "@fluss/n_globals": 0, "@fluss/node_kinds": ["ARGS", "RETURNS"], "@fluss/n_args": 1, "@fluss/n_returns": 0}
    assert result.data["flow"]["descriptors"] == flow
    assert {"id": str(seeded["flow"].pk), "descriptors": flow} in result.data["flows"]
    assert result.data["run"]["descriptors"] == {"@fluss/status": "RUNNING"}
    assert result.data["pythonFlow"]["descriptors"] == {
        "@fluss/status": "PUBLISHED",
        "@fluss/physical": True,
        "@fluss/effect": "IRREVERSIBLE",
        "@fluss/runtime": "monty-0.1",
        "@fluss/n_args": 1,
        "@fluss/n_returns": 0,
    }
    assert result.data["pythonRun"]["descriptors"] == {"@fluss/status": "RUNNING"}
    # A structure that declares no descriptors has none.
    assert result.data["workspace"]["descriptors"] == {}

    declared = {s["identifier"]: [d["key"] for d in s["descriptors"]] for s in service.manifest()["structures"]}
    for field, identifier in (("workspace", "@fluss/workspace"), ("flow", "@fluss/flow"), ("run", "@fluss/run"), ("pythonFlow", "@fluss/pythonflow"), ("pythonRun", "@fluss/pythonrun")):
        assert set(result.data[field]["descriptors"]) == set(declared[identifier])


async def test_the_field_answers_what_the_signal_carried(intake, aexecute, authenticated_context):  # noqa: F811
    seeded = await _seed(aexecute, authenticated_context)

    (received,) = await sync_to_async(intake.of)("@fluss/pythonflow")
    result = await aexecute("query ($id: ID!) { pythonFlow(id: $id) { descriptors } }", {"id": str(seeded["pythonFlow"].pk)})
    assert not result.errors, result.errors
    assert result.data["pythonFlow"]["descriptors"] == received["json"]["descriptors"] != {}

    (received,) = await sync_to_async(intake.of)("@fluss/flow")
    result = await aexecute("query ($id: ID!) { flow(id: $id) { descriptors } }", {"id": str(seeded["flow"].pk)})
    assert not result.errors, result.errors
    assert result.data["flow"]["descriptors"] == received["json"]["descriptors"] != {}


REQUIRED = """
    query ($flows: [RequiresInput!]!, $pythonFlows: [RequiresInput!]!, $runs: [RequiresInput!]!) {
        flows(filters: { requires: $flows }) { id }
        pythonFlows(filters: { requires: $pythonFlows }) { id }
        pythonRuns(filters: { requires: $runs }) { id }
    }
"""


async def _required(aexecute, flows: list, python_flows: list, runs: list) -> dict[str, set[str]]:
    result = await aexecute(REQUIRED, {"flows": flows, "pythonFlows": python_flows, "runs": runs})
    assert not result.errors, result.errors
    return {field: {row["id"] for row in rows} for field, rows in result.data.items()}


async def test_a_port_requires_is_answered_from_the_stored_descriptors(aexecute, authenticated_context):
    seeded = await _seed(aexecute, authenticated_context)
    # createWorkspace's flow takes no argument: what a schedule can start.
    created = await aexecute("mutation { createWorkspace(input: {title: \"Scheduled\"}) { id } }")
    assert not created.errors, created.errors
    scheduled = await Flow.objects.aget(workspace_id=created.data["createWorkspace"]["id"])
    flow, python_flow, python_run = str(seeded["flow"].pk), str(seeded["pythonFlow"].pk), str(seeded["pythonRun"].pk)

    no_args = [{"key": "@fluss/n_args", "operator": "EQUALS", "value": 0}]
    assert (await _required(aexecute, no_args, no_args, []))["flows"] == {str(scheduled.pk)}
    one_or_more = [{"key": "@fluss/n_args", "operator": "GTE", "value": 1}]
    assert await _required(aexecute, one_or_more, one_or_more, [{"key": "@fluss/status", "operator": "EQUALS", "value": "RUNNING"}]) == {"flows": {flow}, "pythonFlows": {python_flow}, "pythonRuns": {python_run}}
    assert (await _required(aexecute, [{"key": "@fluss/node_kinds", "operator": "CONTAINS", "value": "ARGS"}], [], []))["flows"] == {flow, str(scheduled.pk)}

    # A retrying runner takes only what is safe to call again.
    safe = [{"key": "@fluss/effect", "operator": "IN", "value": ["NONE", "REPEATABLE"]}]
    assert (await _required(aexecute, [], safe, []))["pythonFlows"] == set()

    # A key fluss does not declare is refused, not ignored.
    result = await aexecute(REQUIRED, {"flows": [{"key": "@fluss/colour", "operator": "EQUALS", "value": "red"}], "pythonFlows": [], "runs": []})
    assert result.errors and "not a descriptor here" in result.errors[0].message


async def test_a_status_change_is_stored_and_the_setup_job_repairs_what_is_owed(aexecute, authenticated_context):
    seeded = await _seed(aexecute, authenticated_context)
    python_run = seeded["pythonRun"]
    python_run.status = "COMPLETED"
    await python_run.asave(update_fields=["status"])
    completed = [{"key": "@fluss/status", "operator": "EQUALS", "value": "COMPLETED"}]
    assert (await _required(aexecute, [], [], completed))["pythonRuns"] == {str(python_run.pk)}

    # A row from before its descriptors were stored owes them; the setup job states them.
    await Flow.objects.filter(pk=seeded["flow"].pk).aupdate(stored_descriptors={})
    await sync_to_async(call_command)("restore_descriptors")
    assert (await Flow.objects.aget(pk=seeded["flow"].pk)).stored_descriptors["@fluss/n_args"] == 1


async def test_a_sweep_for_one_organization_claims_only_its_rows(authenticated_context):
    """Every organization has the agent and its own schedule: a run must not do another's work."""
    user, org = authenticated_context.request.user, authenticated_context.request.organization
    elsewhere = await Organization.objects.acreate(slug="elsewhere")
    mine = await Workspace.objects.acreate(title="mine", description="Segment nuclei", creator=user, organization=org)
    theirs = await Workspace.objects.acreate(title="theirs", description="Track cells", creator=user, organization=elsewhere)
    await Workspace.objects.filter(pk__in=[mine.pk, theirs.pk]).aupdate(embedding_model="another-model")

    def stale(organization: str | None) -> set[int]:
        return set(stale_queryset(Workspace, organization).values_list("pk", flat=True))

    assert await sync_to_async(stale)("elsewhere") == {theirs.pk}
    assert await sync_to_async(stale)(org.slug) == {mine.pk}
    assert await sync_to_async(stale)(None) == {mine.pk, theirs.pk}

    # The action itself, as rekuest runs it for one organization.
    result = await sync_to_async(agent.actions["reembed_stale"].function)(organization="elsewhere")
    assert result == {"reembedded": 1}
    assert await sync_to_async(stale)(None) == {mine.pk}
    assert (await Workspace.objects.aget(pk=theirs.pk)).embedding_model == engine.model_id()

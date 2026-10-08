"""``descriptors`` on fluss's types: what an object says about itself, from its structure's declaration.

One declaration (``fluss_server.service``) feeds the manifest, the signals and this field, so the
tests hold the three to each other: the field answers what a signal about the object carries, in
the keys the manifest declares. And the agent's sweep, run for one organization, does only that
organization's share.
"""

import uuid

import pytest
from asgiref.sync import sync_to_async
from authentikate.models import Organization

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


@sync_to_async
def _seed(ctx) -> dict:
    """One object of every structure fluss hosts, in the context's organization."""
    user, org = ctx.request.user, ctx.request.organization
    workspace = Workspace.objects.create(title="Described", creator=user, organization=org)
    flow = Flow.objects.create(
        workspace=workspace, title="Described flow", hash=uuid.uuid4().hex, creator=user, organization=org,
        graph={"nodes": [], "edges": [], "globals": []}, nodes=[{"id": "a"}, {"id": "b"}, {"id": "c"}], edges=[{"id": "ab"}, {"id": "bc"}], brittle=True,
    )
    run = Run.objects.create(flow=flow, task_id=uuid.uuid4().hex)
    python_flow = PythonFlow.objects.create(
        organization=org, creator=user, title="moves", source="def main(): pass", runtime="monty-0.1", hash=uuid.uuid4().hex, status="PUBLISHED",
        manifest=[{"alias": "move_stage", "action_hash": "a", "effect": "IRREVERSIBLE"}],
    )
    python_run = PythonRun.objects.create(flow=python_flow, task_id=uuid.uuid4().hex)
    return {"workspace": workspace, "flow": flow, "run": run, "pythonFlow": python_flow, "pythonRun": python_run}


async def test_an_object_answers_the_descriptors_its_structure_declares(aexecute, authenticated_context):
    seeded = await _seed(authenticated_context)

    result = await aexecute(DESCRIBED, {name: str(obj.pk) for name, obj in seeded.items()})
    assert not result.errors, result.errors

    flow = {"@fluss/version": "1.0alpha", "@fluss/n_nodes": 3, "@fluss/n_edges": 2, "@fluss/brittle": True}
    assert result.data["flow"]["descriptors"] == flow
    assert {"id": str(seeded["flow"].pk), "descriptors": flow} in result.data["flows"]
    assert result.data["run"]["descriptors"] == {"@fluss/status": "RUNNING"}
    assert result.data["pythonFlow"]["descriptors"] == {"@fluss/status": "PUBLISHED", "@fluss/physical": True}
    assert result.data["pythonRun"]["descriptors"] == {"@fluss/status": "RUNNING"}
    # A structure that declares no descriptors has none.
    assert result.data["workspace"]["descriptors"] == {}

    declared = {s["identifier"]: [d["key"] for d in s["descriptors"]] for s in service.manifest()["structures"]}
    for field, identifier in (("workspace", "@fluss/workspace"), ("flow", "@fluss/flow"), ("run", "@fluss/run"), ("pythonFlow", "@fluss/pythonflow"), ("pythonRun", "@fluss/pythonrun")):
        assert set(result.data[field]["descriptors"]) == set(declared[identifier])


async def test_the_field_answers_what_the_signal_carried(intake, aexecute, authenticated_context):  # noqa: F811
    seeded = await _seed(authenticated_context)

    (received,) = await sync_to_async(intake.of)("@fluss/pythonflow")
    result = await aexecute("query ($id: ID!) { pythonFlow(id: $id) { descriptors } }", {"id": str(seeded["pythonFlow"].pk)})
    assert not result.errors, result.errors
    assert result.data["pythonFlow"]["descriptors"] == received["json"]["descriptors"] != {}

    (received,) = await sync_to_async(intake.of)("@fluss/flow")
    result = await aexecute("query ($id: ID!) { flow(id: $id) { descriptors } }", {"id": str(seeded["flow"].pk)})
    assert not result.errors, result.errors
    assert result.data["flow"]["descriptors"] == received["json"]["descriptors"] != {}


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

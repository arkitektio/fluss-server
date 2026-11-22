"""Organization scoping tests.

fluss enforces multi-tenant isolation (mirroring mikro): list queries are
scoped via each type's `get_queryset` -> `build_prescoped_queryset`, and
single-item queries/mutations fetch through `reaktion.scoping` (or an explicit
`flow__organization` filter for the run/snapshot family, whose `flow` FK is
nullable). These tests pin both the helper and the end-to-end enforcement.
"""

import pytest
from kante.context import HttpContext

from reaktion import models, scoping
from tests.utils import AExecute, MakeFlow, MakeRun, MakeWorkspace, data_of

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


CREATE_WORKSPACE = """
mutation ($input: CreateWorkspaceInput!) {
  createWorkspace(input: $input) { id title }
}
"""

WORKSPACES_QUERY = """
query {
  workspaces { id title }
}
"""

FLOWS_QUERY = """
query {
  flows { id title }
}
"""

WORKSPACE_QUERY = """
query ($id: ID!) {
  workspace(id: $id) { id title }
}
"""

FLOW_QUERY = """
query ($id: ID!) {
  flow(id: $id) { id title }
}
"""

UPDATE_WORKSPACE = """
mutation ($input: UpdateWorkspaceInput!) {
  updateWorkspace(input: $input) { id title }
}
"""

EMPTY_GRAPH = {"nodes": [], "edges": [], "globals": []}


# --- helper unit test (mirrors mikro/elektro) --------------------------------


async def test_organization_path() -> None:
    assert scoping.organization_path(models.Workspace) == "organization"
    assert scoping.organization_path(models.Flow) == "organization"
    # ReactiveTemplate is a global catalog with no organization.
    assert scoping.organization_path(models.ReactiveTemplate) is None
    # Run reaches org only via a nullable flow FK -> no auto path.
    assert scoping.organization_path(models.Run) is None


# --- list-query isolation ----------------------------------------------------


async def test_workspaces_list_is_org_scoped(
    aexecute: AExecute,
    authenticated_context: HttpContext,
    other_org_context: HttpContext,
) -> None:
    a = await aexecute(
        CREATE_WORKSPACE,
        {"input": {"title": "Org A WS"}},
        context=authenticated_context,
    )
    assert not a.errors, a.errors
    assert a.data is not None
    a_id = a.data["createWorkspace"]["id"]

    # org B sees none of org A's workspaces
    seen = await aexecute(WORKSPACES_QUERY, context=other_org_context)
    assert not seen.errors, seen.errors
    assert seen.data is not None
    assert a_id not in [w["id"] for w in seen.data["workspaces"]]

    # org A still sees its own
    own = await aexecute(WORKSPACES_QUERY, context=authenticated_context)
    assert a_id in [w["id"] for w in data_of(own)["workspaces"]]


async def test_flows_list_is_org_scoped(
    aexecute: AExecute,
    make_flow: MakeFlow,
    authenticated_context: HttpContext,
    other_org_context: HttpContext,
) -> None:
    flow = await make_flow(context=authenticated_context, title="Org A Flow")
    seen = await aexecute(FLOWS_QUERY, context=other_org_context)
    assert not seen.errors, seen.errors
    assert seen.data is not None
    assert str(flow.pk) not in [f["id"] for f in seen.data["flows"]]


async def test_runs_list_is_org_scoped(
    aexecute: AExecute,
    make_run: MakeRun,
    authenticated_context: HttpContext,
    other_org_context: HttpContext,
) -> None:
    run = await make_run(context=authenticated_context)
    seen = await aexecute("query { runs { id } }", context=other_org_context)
    assert not seen.errors, seen.errors
    assert seen.data is not None
    assert str(run.pk) not in [r["id"] for r in seen.data["runs"]]


# --- single-item cross-org fetch blocked -------------------------------------


async def test_workspace_by_id_cross_org_blocked(
    aexecute: AExecute,
    make_workspace: MakeWorkspace,
    authenticated_context: HttpContext,
    other_org_context: HttpContext,
) -> None:
    ws = await make_workspace(context=authenticated_context, title="Private")
    # owner can read it
    own = await aexecute(
        WORKSPACE_QUERY, {"id": str(ws.pk)}, context=authenticated_context
    )
    assert not own.errors, own.errors
    assert own.data is not None
    assert own.data["workspace"]["id"] == str(ws.pk)
    # other org cannot
    other = await aexecute(
        WORKSPACE_QUERY, {"id": str(ws.pk)}, context=other_org_context
    )
    assert other.errors


async def test_flow_by_id_cross_org_blocked(
    aexecute: AExecute,
    make_flow: MakeFlow,
    authenticated_context: HttpContext,
    other_org_context: HttpContext,
) -> None:
    flow = await make_flow(context=authenticated_context)
    other = await aexecute(FLOW_QUERY, {"id": str(flow.pk)}, context=other_org_context)
    assert other.errors


# --- mutation cross-org blocked ----------------------------------------------


async def test_update_workspace_cross_org_blocked(
    aexecute: AExecute,
    make_workspace: MakeWorkspace,
    authenticated_context: HttpContext,
    other_org_context: HttpContext,
) -> None:
    ws = await make_workspace(context=authenticated_context, title="Owned")
    res = await aexecute(
        UPDATE_WORKSPACE,
        {"input": {"workspace": str(ws.pk), "graph": EMPTY_GRAPH, "title": "Hijacked"}},
        context=other_org_context,
    )
    assert res.errors
    await ws.arefresh_from_db()
    assert ws.title == "Owned"


# --- positive: org stamping --------------------------------------------------


async def test_workspace_stamped_with_context_org(
    aexecute: AExecute,
    authenticated_context: HttpContext,
    other_org_context: HttpContext,
) -> None:
    res_a = await aexecute(
        CREATE_WORKSPACE, {"input": {"title": "A"}}, context=authenticated_context
    )
    res_b = await aexecute(
        CREATE_WORKSPACE, {"input": {"title": "B"}}, context=other_org_context
    )
    assert not res_a.errors and not res_b.errors
    assert res_a.data is not None
    ws_a = await models.Workspace.objects.aget(id=res_a.data["createWorkspace"]["id"])
    ws_b = await models.Workspace.objects.aget(
        id=data_of(res_b)["createWorkspace"]["id"]
    )
    assert ws_a.organization_id == authenticated_context.request.organization.id
    assert ws_b.organization_id == other_org_context.request.organization.id
    assert ws_a.organization_id != ws_b.organization_id

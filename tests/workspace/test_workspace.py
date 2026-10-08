"""Workspace mutations executed against the schema: createWorkspace + updateWorkspace."""

import pytest

from reaktion.models import Flow, Workspace

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


CREATE_WORKSPACE = """
mutation ($input: CreateWorkspaceInput!) {
  createWorkspace(input: $input) { id title }
}
"""

UPDATE_WORKSPACE = """
mutation ($input: UpdateWorkspaceInput!) {
  updateWorkspace(input: $input) { id title }
}
"""

EMPTY_GRAPH = {"nodes": [], "edges": [], "globals": []}


async def test_create_workspace(aexecute):
    res = await aexecute(CREATE_WORKSPACE, {"input": {"title": "My Workspace"}})
    assert not res.errors, res.errors
    assert res.data["createWorkspace"]["title"] == "My Workspace"
    # createWorkspace also mints an initial flow.
    ws_id = res.data["createWorkspace"]["id"]
    assert await Workspace.objects.filter(id=ws_id).aexists()
    assert await Flow.objects.filter(workspace_id=ws_id).aexists()


async def test_create_workspace_autonames_when_title_missing(aexecute):
    res = await aexecute(CREATE_WORKSPACE, {"input": {}})
    assert not res.errors, res.errors
    assert res.data["createWorkspace"]["title"]  # namegenerator default


async def test_update_workspace(aexecute, make_workspace):
    ws = await make_workspace(title="Before")
    res = await aexecute(
        UPDATE_WORKSPACE,
        {"input": {"workspace": str(ws.id), "graph": EMPTY_GRAPH, "title": "After"}},
    )
    assert not res.errors, res.errors
    assert res.data["updateWorkspace"]["id"] == str(ws.id)
    # updateWorkspace upserts a Flow for the posted graph under the workspace.
    assert await Flow.objects.filter(workspace_id=ws.id, title="After").aexists()


async def test_create_workspace_stamps_organization(aexecute, authenticated_context):
    res = await aexecute(CREATE_WORKSPACE, {"input": {"title": "Org Stamped"}})
    assert not res.errors, res.errors
    ws = await Workspace.objects.aget(id=res.data["createWorkspace"]["id"])
    assert ws.organization_id == authenticated_context.request.organization.id
    assert ws.creator_id == authenticated_context.request.user.id


def _node(node_id: str, kind: str, ins: list, outs: list) -> dict:
    return {"id": node_id, "kind": kind, "position": {"x": 0, "y": 0}, "ins": ins, "outs": outs, "constants": [], "voids": [], "constantsMap": {}, "globalsMap": {}}


async def test_update_workspace_rejects_a_malformed_port(aexecute, make_workspace):
    """A LIST port without its item child is rejected by the graph validation, not stored."""
    ws = await make_workspace(title="Strict")
    bad = {"nodes": [_node("1", "ARGS", [[]], [[{"key": "xs", "kind": "LIST", "nullable": False}]])], "edges": [], "globals": []}
    res = await aexecute(UPDATE_WORKSPACE, {"input": {"workspace": str(ws.id), "graph": bad}})
    assert res.errors and "exactly one child" in res.errors[0].message
    assert not await Flow.objects.filter(workspace_id=ws.id, title="Untitled Workspace").aexists()


async def test_update_workspace_round_trips_a_valid_graph(aexecute, make_workspace):
    """A valid graph is normalised, stored and read back through the flow's typed graph."""
    ws = await make_workspace(title="Round trip")
    out_port = {"key": "xs", "kind": "LIST", "nullable": False, "children": [{"key": "...", "kind": "STRUCTURE", "identifier": "@mikro/image", "nullable": False}]}
    graph = {"nodes": [_node("1", "ARGS", [[]], [[out_port]]), _node("2", "RETURNS", [[]], [[]])], "edges": [], "globals": []}
    res = await aexecute(UPDATE_WORKSPACE, {"input": {"workspace": str(ws.id), "graph": graph, "title": "Typed"}})
    assert not res.errors, res.errors

    flow = await Flow.objects.aget(workspace_id=ws.id, title="Typed")
    node = flow.graph["nodes"][0]
    assert node["outs"][0][0]["children"][0]["identifier"] == "@mikro/image"
    assert node["title"] is None  # optional on both write and read

    read = await aexecute("query($id: ID!) { flow(id: $id) { graph { nodes { id kind outs { key kind children { key identifier } } } } } }", {"id": str(flow.id)})
    assert not read.errors, read.errors
    assert read.data["flow"]["graph"]["nodes"][0]["outs"][0][0]["children"][0]["identifier"] == "@mikro/image"


async def test_update_workspace_accepts_an_enum_port_naming_its_enum(aexecute, make_workspace):
    """An ENUM port may carry the identifier of the enum its choices came from, as the SDK sends it."""
    ws = await make_workspace(title="Enum")
    port = {"key": "positioner", "kind": "ENUM", "nullable": False, "identifier": "@stage/positioner", "choices": [{"value": "x", "label": "X"}, {"value": "y", "label": "Y"}]}
    graph = {"nodes": [_node("1", "ARGS", [[]], [[port]]), _node("2", "RETURNS", [[]], [[]])], "edges": [], "globals": []}
    res = await aexecute(UPDATE_WORKSPACE, {"input": {"workspace": str(ws.id), "graph": graph, "title": "Enum"}})
    assert not res.errors, res.errors

    flow = await Flow.objects.aget(workspace_id=ws.id, title="Enum")
    read = await aexecute("query($id: ID!) { flow(id: $id) { graph { nodes { outs { key kind identifier } } } } }", {"id": str(flow.id)})
    assert not read.errors, read.errors
    assert read.data["flow"]["graph"]["nodes"][0]["outs"][0][0] == {"key": "positioner", "kind": "ENUM", "identifier": "@stage/positioner"}


async def test_update_workspace_defaults_omitted_value_maps(aexecute, make_workspace):
    """``constantsMap``/``globalsMap`` are optional on the wire but always stored as maps.

    They carry no SDL default (an ``= {}`` default on the ``ValueMap`` custom scalar is
    unrepresentable as an AST literal and breaks client codegen), so omitting them sends
    ``null`` -- which must still round-trip as ``{}`` because the matching ``GraphNode``
    output fields are non-null.
    """
    ws = await make_workspace(title="Defaulted maps")
    bare = {"id": "1", "kind": "ARGS", "position": {"x": 0, "y": 0}, "ins": [[]], "outs": [[]], "constants": [], "voids": []}
    graph = {"nodes": [bare], "edges": [], "globals": []}
    res = await aexecute(UPDATE_WORKSPACE, {"input": {"workspace": str(ws.id), "graph": graph, "title": "Defaulted"}})
    assert not res.errors, res.errors

    flow = await Flow.objects.aget(workspace_id=ws.id, title="Defaulted")
    assert flow.graph["nodes"][0]["constants_map"] == {}
    assert flow.graph["nodes"][0]["globals_map"] == {}

    read = await aexecute("query($id: ID!) { flow(id: $id) { graph { nodes { id constantsMap globalsMap } } } }", {"id": str(flow.id)})
    assert not read.errors, read.errors
    assert read.data["flow"]["graph"]["nodes"][0]["constantsMap"] == {}
    assert read.data["flow"]["graph"]["nodes"][0]["globalsMap"] == {}

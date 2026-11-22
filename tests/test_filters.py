"""Exercise the filter_type / order_type wiring at runtime (not just in the SDL).

Confirms the migrated filters actually run (the old `name__icontains` search
referenced a non-existent field) and that ordering is applied.
"""

import pytest

from tests.utils import AExecute, MakeFlow, MakeReactiveTemplate, MakeWorkspace

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


WORKSPACES = """
query ($filters: WorkspaceFilter, $ordering: [WorkspaceOrder!]) {
  workspaces(filters: $filters, ordering: $ordering) { id title }
}
"""

FLOWS = """
query ($filters: FlowFilter) {
  flows(filters: $filters) { id title }
}
"""

TEMPLATES = """
query ($filters: ReactiveTemplateFilter) {
  reactiveTemplates(filters: $filters) { id implementation }
}
"""


async def test_workspace_search_filter(
    aexecute: AExecute, make_workspace: MakeWorkspace
) -> None:
    await make_workspace(title="Alpha Pipeline")
    await make_workspace(title="Beta Pipeline")
    res = await aexecute(WORKSPACES, {"filters": {"search": "alpha"}})
    assert not res.errors, res.errors
    assert res.data is not None
    titles = [w["title"] for w in res.data["workspaces"]]
    assert titles == ["Alpha Pipeline"]


async def test_workspace_ids_filter(
    aexecute: AExecute, make_workspace: MakeWorkspace
) -> None:
    a = await make_workspace(title="A")
    await make_workspace(title="B")
    res = await aexecute(WORKSPACES, {"filters": {"ids": [str(a.pk)]}})
    assert not res.errors, res.errors
    assert res.data is not None
    assert [w["id"] for w in res.data["workspaces"]] == [str(a.pk)]


async def test_workspace_ordering(
    aexecute: AExecute, make_workspace: MakeWorkspace
) -> None:
    await make_workspace(title="Zeta")
    await make_workspace(title="Alpha")
    res = await aexecute(WORKSPACES, {"ordering": [{"title": "ASC"}]})
    assert not res.errors, res.errors
    assert res.data is not None
    titles = [w["title"] for w in res.data["workspaces"]]
    assert titles == sorted(titles)
    assert titles[0] == "Alpha"


async def test_flow_ids_filter(aexecute: AExecute, make_flow: MakeFlow) -> None:
    f = await make_flow(title="Flow A")
    await make_flow(title="Flow B")
    res = await aexecute(FLOWS, {"filters": {"ids": [str(f.pk)]}})
    assert not res.errors, res.errors
    assert res.data is not None
    assert [x["id"] for x in res.data["flows"]] == [str(f.pk)]


async def test_reactive_template_implementations_filter(
    aexecute: AExecute, make_reactive_template: MakeReactiveTemplate
) -> None:
    zip_tpl = await make_reactive_template(implementation="ZIP")
    await make_reactive_template(implementation="WITHLATEST")
    res = await aexecute(TEMPLATES, {"filters": {"implementations": ["ZIP"]}})
    assert not res.errors, res.errors
    assert res.data is not None
    impls = {t["implementation"] for t in res.data["reactiveTemplates"]}
    assert impls == {"ZIP"}
    assert str(zip_tpl.pk) in [t["id"] for t in res.data["reactiveTemplates"]]

"""Flow queries executed against the schema."""

import pytest

from tests.utils import AExecute, MakeFlow

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


FLOW_QUERY = """
query ($id: ID!) {
  flow(id: $id) { id title hash }
}
"""

FLOWS_QUERY = """
query {
  flows { id title }
}
"""


async def test_flow_query(aexecute: AExecute, make_flow: MakeFlow) -> None:
    flow = await make_flow(title="My Flow")
    res = await aexecute(FLOW_QUERY, {"id": str(flow.pk)})
    assert not res.errors, res.errors
    assert res.data is not None
    assert res.data["flow"]["id"] == str(flow.pk)
    assert res.data["flow"]["title"] == "My Flow"


async def test_flows_list(aexecute: AExecute, make_flow: MakeFlow) -> None:
    flow = await make_flow(title="Listed Flow")
    res = await aexecute(FLOWS_QUERY)
    assert not res.errors, res.errors
    assert res.data is not None
    ids = [f["id"] for f in res.data["flows"]]
    assert str(flow.pk) in ids


async def test_flow_query_not_found(aexecute: AExecute) -> None:
    res = await aexecute(FLOW_QUERY, {"id": "999999"})
    assert res.errors

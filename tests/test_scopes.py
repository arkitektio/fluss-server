"""What an app may do here is what its token's scopes say: every root field asks for one of fluss's
own (the ``@auth`` directive publishes it, a generated client gathers it), and `fluss_all` stands
for all of them."""

import pytest
from kante.context import HttpContext, UniversalRequest
from strawberry.http.temporal_response import TemporalResponse

from arkitekt_service.graphql import scope_gaps
from fluss_server.schema import schema

MAKE_WORKSPACE = 'mutation { createWorkspace(input: {title: "scoped"}) { id } }'
WORKSPACES = "query { workspaces { id } }"


def _as(token: str) -> HttpContext:
    return HttpContext(request=UniversalRequest(_extensions={}), response=TemporalResponse(), headers={"Authorization": f"Bearer {token}"}, type="http")


def _reason(result) -> str | None:
    return result.errors[0].extensions.get("reason") if result.errors else None


def test_every_root_field_asks_for_a_scope_fluss_declares():
    assert scope_gaps(schema) == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_an_app_granted_reads_reads_and_writes_nothing(backend_stack):
    assert (await schema.execute(WORKSPACES, context_value=_as("readertest"))).errors is None
    refused = await schema.execute(MAKE_WORKSPACE, context_value=_as("readertest"))
    assert _reason(refused) == "INSUFFICIENT_SCOPE"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_the_all_scope_writes(backend_stack):
    made = await schema.execute(MAKE_WORKSPACE, context_value=_as("test"))
    assert made.errors is None, made.errors

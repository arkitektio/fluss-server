"""Workspaces and flows embed their title + description on save; ``search`` is hybrid and ranked.

Real model (potion-base-8M), real Postgres with pgvector -- what the service runs. Where a
test needs rows at *known* distances from the query it writes the vectors directly: ``e0`` is
the real embedding of the query, ``_vec(d)`` a unit vector at cosine distance ``d`` from it.
"""

import math
import uuid

import numpy as np
import pytest
from asgiref.sync import sync_to_async
from django.test import override_settings

from embeddings import engine
from embeddings.healer import reembed_all, reembed_stale
from reaktion.models import Flow, Workspace

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]

QUERY = "detect cells"

WORKSPACES = """
query ($filters: WorkspaceFilter, $ordering: [WorkspaceOrder!]) {
  workspaces(filters: $filters, ordering: $ordering) { title }
}
"""
FLOWS = """
query ($filters: FlowFilter, $ordering: [FlowOrder!]) {
  flows(filters: $filters, ordering: $ordering) { title }
}
"""


@sync_to_async
def _workspace(ctx, title: str, description: str | None = None) -> Workspace:
    return Workspace.objects.create(title=title, description=description, creator=ctx.request.user, organization=ctx.request.organization)


@sync_to_async
def _flow(ctx, title: str, description: str | None = None) -> Flow:
    return Flow.objects.create(title=title, description=description, hash=uuid.uuid4().hex, creator=ctx.request.user, organization=ctx.request.organization)


MODELS = [
    pytest.param(Workspace, _workspace, WORKSPACES, "workspaces", id="workspace"),
    pytest.param(Flow, _flow, FLOWS, "flows", id="flow"),
]


def _unit_orthogonal(e0: np.ndarray) -> np.ndarray:
    axis = np.zeros_like(e0)
    axis[int(np.argmin(np.abs(e0)))] = 1.0
    u = axis - float(np.dot(axis, e0)) * e0
    return u / np.linalg.norm(u)


def _vec(e0: np.ndarray, distance: float) -> list[float]:
    theta = math.acos(1.0 - distance)
    return (math.cos(theta) * e0 + math.sin(theta) * _unit_orthogonal(e0)).astype(float).tolist()


async def _pin(model, row, e0, distance, embedding_model=None):
    await model.objects.filter(pk=row.pk).aupdate(embedding=_vec(e0, distance) if distance is not None else None, embedding_model=embedding_model or engine.model_id())


async def _titles(aexecute, query, search, ordering=None):
    res = await aexecute(query, {"filters": {"search": search}, "ordering": ordering or []})
    assert not res.errors, res.errors
    return [row["title"] for row in next(iter(res.data.values()))]


@pytest.mark.parametrize(("model", "seed", "query", "field"), MODELS)
async def test_create_embeds(authenticated_context, model, seed, query, field):
    row = await seed(authenticated_context, "Segment nuclei", "Find cell nuclei in a fluorescence image")
    await row.arefresh_from_db()
    assert row.embedding is not None and len(row.embedding) == 256
    assert abs(sum(x * x for x in row.embedding) - 1.0) < 1e-4
    assert row.embedding_model == engine.model_id()


async def test_editing_the_description_reembeds(authenticated_context):
    ws = await _workspace(authenticated_context, "Export", "Write a table to a spreadsheet")
    before = list((await Workspace.objects.aget(pk=ws.pk)).embedding)
    ws = await Workspace.objects.aget(pk=ws.pk)
    ws.description = "Detect mitochondria in electron micrographs"
    await ws.asave()
    assert list((await Workspace.objects.aget(pk=ws.pk)).embedding) != before


async def test_blank_text_stores_null_and_is_complete(authenticated_context):
    ws = await _workspace(authenticated_context, "  ", None)
    await ws.arefresh_from_db()
    assert ws.embedding is None and ws.embedding_model == engine.model_id()
    assert await sync_to_async(reembed_stale)(Workspace) == 0


async def test_healer_reembeds_rows_of_another_model(authenticated_context):
    ws = await _workspace(authenticated_context, "Blur", "Gaussian blur of an image")
    fl = await _flow(authenticated_context, "Blur v2", "Gaussian blur, faster")
    for model, row in ((Workspace, ws), (Flow, fl)):
        await model.objects.filter(pk=row.pk).aupdate(embedding=None, embedding_model="some/older-model")
    assert await sync_to_async(reembed_all)([Workspace, Flow]) == 2
    for model, row in ((Workspace, ws), (Flow, fl)):
        fresh = await model.objects.aget(pk=row.pk)
        assert fresh.embedding is not None and fresh.embedding_model == engine.model_id()
    assert await sync_to_async(reembed_all)([Workspace, Flow]) == 0


@pytest.mark.parametrize(("model", "seed", "query", "field"), MODELS)
async def test_semantic_match_without_substring(aexecute, authenticated_context, model, seed, query, field):
    await seed(authenticated_context, "Segment nuclei", "Find cell nuclei in a fluorescence image and detect every cell")
    await seed(authenticated_context, "Export spreadsheet", "Write a table to an xlsx file on disk")
    titles = await _titles(aexecute, query, QUERY)
    assert "Segment nuclei" in titles and "Export spreadsheet" not in titles


@pytest.mark.parametrize(("model", "seed", "query", "field"), MODELS)
async def test_lexical_only_when_disabled(aexecute, authenticated_context, model, seed, query, field):
    await seed(authenticated_context, "Detect cells", None)
    await seed(authenticated_context, "Segment nuclei", "detect cells in an image")
    with override_settings(EMBEDDINGS={**engine._settings(), "ENABLED": False}):
        assert await _titles(aexecute, query, QUERY) == ["Detect cells"]


@pytest.mark.parametrize(("model", "seed", "query", "field"), MODELS)
async def test_ranking_lexical_first_then_by_distance(aexecute, authenticated_context, model, seed, query, field):
    e0 = np.asarray(engine.embed_query(QUERY))
    await _pin(model, await seed(authenticated_context, "Far"), e0, 0.5)
    await _pin(model, await seed(authenticated_context, "Near"), e0, 0.1)
    await _pin(model, await seed(authenticated_context, "Mid"), e0, 0.3)
    await _pin(model, await seed(authenticated_context, "Beyond"), e0, 0.7)
    await _pin(model, await seed(authenticated_context, "Detect cells here"), e0, None)
    assert await _titles(aexecute, query, QUERY) == ["Detect cells here", "Near", "Mid", "Far"]


@pytest.mark.parametrize(("model", "seed", "query", "field"), MODELS)
async def test_stale_embedding_model_is_not_a_vector_hit(aexecute, authenticated_context, model, seed, query, field):
    e0 = np.asarray(engine.embed_query(QUERY))
    await _pin(model, await seed(authenticated_context, "Old model near"), e0, 0.05, "some/older-model")
    await _pin(model, await seed(authenticated_context, "Old model detect cells"), e0, 0.05, "some/older-model")
    assert await _titles(aexecute, query, QUERY) == ["Old model detect cells"]


@pytest.mark.parametrize(("model", "seed", "query", "field"), MODELS)
async def test_explicit_ordering_replaces_the_ranking(aexecute, authenticated_context, model, seed, query, field):
    e0 = np.asarray(engine.embed_query(QUERY))
    await _pin(model, await seed(authenticated_context, "Zeta"), e0, 0.1)
    await _pin(model, await seed(authenticated_context, "Alpha"), e0, 0.4)
    assert await _titles(aexecute, query, QUERY) == ["Zeta", "Alpha"]
    assert await _titles(aexecute, query, QUERY, ordering=[{"title": "ASC"}]) == ["Alpha", "Zeta"]


async def test_unloadable_model_degrades_to_substring(aexecute, authenticated_context):
    e0 = np.asarray(engine.embed_query(QUERY))
    await _pin(Workspace, await _workspace(authenticated_context, "Near"), e0, 0.05)
    await _workspace(authenticated_context, "Detect cells")
    try:
        with override_settings(EMBEDDINGS={**engine._settings(), "MODEL_PATH": "/nonexistent/embeddings"}):
            engine.reset()
            assert await _titles(aexecute, WORKSPACES, QUERY) == ["Detect cells"]
    finally:
        engine.reset()

"""Pytest fixtures for the fluss test suite.

Ported from elektro's strategy: a dockerized Postgres backend (dokker), an
``aexecute`` GraphQL helper, authenticated + cross-org contexts, and per-model
factory fixtures. fluss has no object store, so the S3/minio/zarr fixtures from
elektro are intentionally omitted.
"""

import os
import time
import uuid

import psycopg
import pytest
from asgiref.sync import sync_to_async

from authentikate.models import Client, Membership, Organization, User
from django.contrib.contenttypes.management import create_contenttypes
from django.db.models.signals import post_migrate
from kante.context import HttpContext, UniversalRequest
from strawberry.http.temporal_response import TemporalResponse
from dokker import testing


@pytest.fixture(scope="session")
def backend_stack():
    """Bring up the Postgres (+ Redis) backend from tests/integration/docker-compose.yaml."""
    docker_compose_path = os.path.join(os.path.dirname(__file__), "integration", "docker-compose.yaml")

    with testing(docker_compose_path) as e:
        e.inspect()

        e.down()

        e.up()

        # compose only waits for postgres to *start*, not to accept connections,
        # so poll until it answers before letting pytest-django configure the DB.
        deadline = time.monotonic() + 30
        while True:
            try:
                with psycopg.connect(
                    dbname="testdb",
                    user="test",
                    password="test",
                    host="localhost",
                    port=5555,
                    connect_timeout=1,
                ) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                break
            except psycopg.OperationalError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.2)

        # The suite builds its schema with run-syncdb (migrations disabled), so the
        # `vector` extension migration never runs here -- but CREATE TABLE for the
        # embedding columns (Workspace/Flow.embedding) needs the type to exist. Install
        # it into template1 so the test database pytest-django creates from it
        # inherits it, and into testdb itself for anything connecting directly.
        for dbname in ("template1", "testdb"):
            with psycopg.connect(dbname=dbname, user="test", password="test", host="localhost", port=5555, autocommit=True) as connection:
                connection.execute("CREATE EXTENSION IF NOT EXISTS vector")

        yield


@pytest.fixture(scope="session", autouse=True)
def embedding_model_warm():
    """Load the embedding model once per session, outside any test's DB transaction.

    Every save of a Workspace / Flow embeds its text, so the first one would otherwise pay
    the model load (a one-time download into the Hugging Face cache on a cold box) inside a
    test.
    """
    from embeddings import engine

    engine.warm_up()
    yield


@pytest.fixture(scope="session")
def django_db_modify_db_settings(backend_stack):
    """Start the backend services before pytest-django configures the test DB."""
    yield


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    # Every transaction=True test teardown flushes the DB and re-fires
    # post_migrate, which rebuilds all contenttypes and permissions from the
    # model registry (~1s per test). The rows never change between tests, so
    # snapshot them once and swap the rebuild for a bulk re-insert with the
    # original pks (keeps guardian FKs and the ContentType pk cache valid).
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    with django_db_blocker.unblock():
        contenttypes = list(ContentType.objects.all())
        permissions = list(Permission.objects.all())

    post_migrate.disconnect(dispatch_uid="django.contrib.auth.management.create_permissions")
    post_migrate.disconnect(create_contenttypes)

    def restore_contenttypes_and_permissions(sender, **kwargs):
        # post_migrate fires once per app config on flush; restore once.
        if getattr(sender, "label", None) != "contenttypes":
            return
        ContentType.objects.bulk_create(contenttypes, ignore_conflicts=True)
        Permission.objects.bulk_create(permissions, ignore_conflicts=True)

    post_migrate.connect(
        restore_contenttypes_and_permissions,
        dispatch_uid="tests.restore_contenttypes_and_permissions",
    )
    yield

    # The async tests run sync ORM code in asgiref's executor threads, whose
    # connections outlive the tests and block dropping the test database
    # ("database is being accessed by other users"). Kill them before
    # pytest-django's teardown drops the database.
    from django.db import connections

    with django_db_blocker.unblock():
        with connections["default"].cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = current_database() AND pid <> pg_backend_pid()"
            )
        connections.close_all()


@pytest.fixture(scope="function")
def authenticated_context(db, backend_stack) -> HttpContext:
    # Match the identity the static "test" token resolves to (settings_test
    # STATIC_TOKENS), so the org/user on this context is the same one the
    # schema's AuthentikateExtension authenticates as at resolve time.
    user, _ = User.objects.get_or_create(
        sub="1", iss="static_issuer", defaults={"username": "static_issuer_1"}
    )
    client, _ = Client.objects.get_or_create(client_id="oinsoins")
    org, _ = Organization.objects.get_or_create(slug="static_org")
    membership, _ = Membership.objects.get_or_create(user=user, organization=org)

    request = UniversalRequest(
        _extensions={"token": "test"},
        _client=client,  # type: ignore
        _user=user,  # type: ignore
        _organization=org,  # type: ignore
    )
    request.set_membership(membership)  # type: ignore

    return HttpContext(
        request=request,
        response=TemporalResponse(),
        headers={"Authorization": "Bearer test"},
        type="http",
    )


@pytest.fixture(scope="function")
def other_org_context(db, backend_stack) -> HttpContext:
    """A context for a user in a different organization (static token "othertest")."""
    user, _ = User.objects.get_or_create(
        sub="9", iss="static_issuer", defaults={"username": "static_issuer_9"}
    )
    client, _ = Client.objects.get_or_create(client_id="oinsoins")
    org, _ = Organization.objects.get_or_create(slug="other_org")
    membership, _ = Membership.objects.get_or_create(user=user, organization=org)

    request = UniversalRequest(
        _extensions={"token": "othertest"},
        _client=client,  # type: ignore
        _user=user,  # type: ignore
        _organization=org,  # type: ignore
    )
    request.set_membership(membership)  # type: ignore

    return HttpContext(
        request=request,
        response=TemporalResponse(),
        headers={"Authorization": "Bearer othertest"},
        type="http",
    )


# ---------------------------------------------------------------------------
# GraphQL execution helper + prerequisite-row factories.
# ---------------------------------------------------------------------------


@pytest.fixture
def aexecute(authenticated_context):
    """Run a GraphQL document against the schema, defaulting to the authed context."""
    from fluss_server.schema import schema

    async def _run(query, variables=None, context=None):
        return await schema.execute(
            query,
            variable_values=variables or {},
            context_value=context or authenticated_context,
        )

    return _run


@pytest.fixture
def make_workspace(authenticated_context):
    """Factory: create a Workspace row."""
    from reaktion.models import Workspace

    @sync_to_async
    def _make(context=None, title="Workspace"):
        ctx = context or authenticated_context
        return Workspace.objects.create(
            title=title,
            creator=ctx.request.user,
            organization=ctx.request.organization,
        )

    return _make


@pytest.fixture
def make_flow(authenticated_context):
    """Factory: create a Flow row (organization is NOT NULL; hash is unique per workspace)."""
    from reaktion.models import Flow, Workspace

    @sync_to_async
    def _make(context=None, workspace=None, title="Flow", graph=None):
        ctx = context or authenticated_context
        if workspace is None:
            workspace = Workspace.objects.create(
                title=f"ws-{uuid.uuid4().hex}",
                creator=ctx.request.user,
                organization=ctx.request.organization,
            )
        return Flow.objects.create(
            workspace=workspace,
            title=title,
            hash=uuid.uuid4().hex,
            graph=graph or {"nodes": [], "edges": [], "globals": []},
            creator=ctx.request.user,
            organization=ctx.request.organization,
        )

    return _make


@pytest.fixture
def make_run(authenticated_context, make_flow):
    """Factory: create a Run row (defaults to a freshly minted flow)."""
    from reaktion.models import Run

    @sync_to_async
    def _make(flow, task_id=None):
        return Run.objects.create(
            flow=flow,
            task_id=task_id or uuid.uuid4().hex,
        )

    async def _wrap(context=None, flow=None, task_id=None):
        if flow is None:
            flow = await make_flow(context=context)
        return await _make(flow, task_id)

    return _wrap


@pytest.fixture
def make_snapshot(authenticated_context):
    """Factory: create a Snapshot row (t is required)."""
    from reaktion.models import Snapshot

    @sync_to_async
    def _make(run, t=0):
        return Snapshot.objects.create(run=run, t=t)

    return _make


@pytest.fixture
def make_reactive_template(authenticated_context):
    """Factory: create a ReactiveTemplate row (title+description are unique together)."""
    from reaktion.models import ReactiveTemplate

    @sync_to_async
    def _make(title=None, description=None, implementation="ZIP"):
        return ReactiveTemplate.objects.create(
            title=title or f"tpl-{uuid.uuid4().hex}",
            description=description or "A reactive template",
            implementation=implementation,
        )

    return _make


@pytest.fixture
def make_trace(authenticated_context, make_flow):
    """Factory: create a Trace row (no GraphQL surface; model-level only)."""
    from reaktion.models import Trace

    @sync_to_async
    def _make(flow, provision=None):
        return Trace.objects.create(flow=flow, provision=provision)

    async def _wrap(context=None, flow=None, provision=None):
        if flow is None:
            flow = await make_flow(context=context)
        return await _make(flow, provision)

    return _wrap

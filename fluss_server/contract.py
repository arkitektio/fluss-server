"""What this image answers a hub's installer: ``arkitekt-service <verb>`` (see ``arkitekt_service.contract``).

The installer knows the hub; how this release spells its config is written here, with the
settings it is read by. A key renamed in ``configuration.py`` is renamed in :func:`render` in
the same commit, and no installer has to learn of it.
"""

from __future__ import annotations

from arkitekt_service.contract import JSON, Contract, Description, Descriptor, Facts, Hosts, Needs, Offers, Scope, Signal, Start, Structure, blocks

from fluss_server.configuration import Settings

#: What a token may be allowed to do here: defined at the coordination server when the hub enrols.
SCOPES = [
    Scope(key="fluss_read", description="Read workflow definitions"),
    Scope(key="fluss_write", description="Create and modify workflows"),
    Scope(key="fluss_execute", description="Execute workflows"),
    Scope(key="read", description="Generic read access"),
    Scope(key="write", description="Generic write access"),
]

#: The roles a member of an organization can hold here.
ROLES = [
    Scope(key="admin", description="Full administrative access"),
    Scope(key="user", description="Standard user access"),
    Scope(key="designer", description="Can design workflows"),
    Scope(key="viewer", description="Read-only access"),
]

#: What exists on a hub because this service is there: said here, as data, so the hub knows it from
#: the image. ``service.py`` binds each of these to its model and refuses anything not said here.
HOSTS = Hosts(
    structures=[
        Structure(
            identifier="@fluss/workspace",
            label="Workspace",
            description="A workspace: the container users edit the versions of one flow in.",
        ),
        Structure(
            identifier="@fluss/flow",
            label="Flow",
            description="A flow: one saved, executable version of a workspace's graph of nodes and edges.",
            descriptors=[
                Descriptor(key="@fluss/version", type="STRING", description="Its version label"),
                Descriptor(key="@fluss/n_nodes", type="INT", description="How many nodes its graph has"),
                Descriptor(key="@fluss/n_edges", type="INT", description="How many edges its graph has"),
                Descriptor(key="@fluss/brittle", type="BOOL", description="Whether it fails on any exception"),
            ],
        ),
        Structure(
            identifier="@fluss/run",
            label="Run",
            description="A run: one live execution of a flow for a task.",
            descriptors=[
                Descriptor(key="@fluss/status", type="STRING", description="Where the run stands: RUNNING or COMPLETED"),
            ],
        ),
        Structure(
            identifier="@fluss/pythonflow",
            label="Python Flow",
            description="A Python flow: one immutable version of a flow written as Python source.",
            descriptors=[
                Descriptor(key="@fluss/status", type="STRING", description="Its lifecycle: DRAFT, PUBLISHED or ARCHIVED"),
                Descriptor(key="@fluss/physical", type="BOOL", description="Whether its source may call an action with a PHYSICAL effect"),
            ],
        ),
        Structure(
            identifier="@fluss/pythonrun",
            label="Python Run",
            description="A Python run: one execution of a published Python flow for a task.",
            descriptors=[
                Descriptor(key="@fluss/status", type="STRING", description="Where the run stands: RUNNING, COMPLETED or FAILED"),
            ],
        ),
    ],
    signals=[
        Signal(
            identifier="@fluss/workspace",
            kinds=["CREATED", "UPDATED", "DELETED"],
            description="A workspace was created, changed or deleted.",
        ),
        Signal(
            identifier="@fluss/flow",
            kinds=["CREATED"],
            descriptors=["@fluss/version", "@fluss/n_nodes", "@fluss/n_edges", "@fluss/brittle"],
            description="A flow (a version of a workspace's graph) was created.",
        ),
        Signal(
            identifier="@fluss/run",
            kinds=["CREATED", "UPDATED", "DELETED"],
            descriptors=["@fluss/status"],
            description="A flow run started, changed status (e.g. completed) or was deleted.",
        ),
        Signal(
            identifier="@fluss/pythonflow",
            kinds=["CREATED", "UPDATED", "DELETED"],
            descriptors=["@fluss/status", "@fluss/physical"],
            description="A Python flow version was created, published or archived (UPDATED), or a draft deleted.",
        ),
        Signal(
            identifier="@fluss/pythonrun",
            kinds=["CREATED", "UPDATED", "DELETED"],
            descriptors=["@fluss/status"],
            description="A Python flow run started, finished (COMPLETED/FAILED) or was deleted.",
        ),
    ],
)


def render(facts: Facts) -> dict[str, JSON]:
    """This release's config for the hub ``facts`` describes."""
    document: dict[str, JSON] = blocks.server(facts)
    document["instance"] = blocks.instance(facts)
    hook = blocks.rekuest_hook(facts)
    if hook is not None:
        document["rekuest_hook"] = hook
    return document


contract = Contract(
    description=Description(
        name="fluss",
        identifier="live.arkitekt.fluss",
        summary="Workflows over the hub's actions.",
        needs=Needs(scopes=SCOPES, roles=ROLES, storage=["media"], instance_key=True, peers=["rekuest"]),
        offers=Offers(endpoints={"rekuest_service": "_rekuest/service", "rekuest_hook": "_rekuest/hook"}),
        requires={"rekuest": ">=6"},
        hosts=HOSTS,
    ),
    settings=Settings,
    render=render,
    # How this service is started: there is no script beside it. `arkitekt-service serve`
    # (and `debug`) become these, so they get the container's signals themselves.
    serve=Start(("daphne", "-b", "0.0.0.0", "-p", "80", "--websocket_timeout", "-1", "fluss_server.asgi:application")),
    debug=Start(("python", "manage.py", "runserver", "0.0.0.0:80")),
)

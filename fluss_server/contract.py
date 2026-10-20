"""What this image answers a hub's installer: ``arkitekt-service <verb>`` (see ``arkitekt_service.contract``).

The installer knows the hub; how this release spells its config is written here, with the
settings it is read by. A key renamed in ``configuration.py`` is renamed in :func:`render` in
the same commit, and no installer has to learn of it.
"""

from __future__ import annotations

from arkitekt_service.contract import JSON, Contract, Description, Descriptor, Facts, Hosts, Job, Needs, Offers, Scope, Signal, Start, Structure, blocks

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

#: How many ports a flow is called with and answers with: what a scheduler (no arguments) or a
#: batch runner (exactly one) selects on. One key for both kinds of flow, so one `requires` asks both.
_N_ARGS = Descriptor(key="@fluss/n_args", type="INT", description="How many arguments (inputs) it is called with: 0 for a flow a schedule can start")
_N_RETURNS = Descriptor(key="@fluss/n_returns", type="INT", description="How many values (outputs) it returns")

FLOW_DESCRIPTORS = [
    Descriptor(key="@fluss/n_nodes", type="INT", description="How many nodes its graph has"),
    Descriptor(key="@fluss/n_edges", type="INT", description="How many edges its graph has"),
    Descriptor(key="@fluss/n_globals", type="INT", description="How many global parameters it is configured with: 0 for a flow that runs without a form"),
    Descriptor(
        key="@fluss/node_kinds",
        type="LIST",
        description="The kinds of node its graph runs (REACTIVE, ARGS, RETURNS, REKUEST_MAP, REKUEST_FILTER, AGENT_SUBFLOW): AGENT_SUBFLOW needs an agent to host it",
    ),
    _N_ARGS,
    _N_RETURNS,
]
PYTHON_FLOW_DESCRIPTORS = [
    Descriptor(key="@fluss/status", type="STRING", description="Its publication lifecycle: DRAFT, PUBLISHED or ARCHIVED"),
    Descriptor(key="@fluss/physical", type="BOOL", description="Whether its source may call an action with an IRREVERSIBLE effect"),
    Descriptor(key="@fluss/effect", type="STRING", description="The most consequential effect of an action its source may call: NONE, REPEATABLE, UNKNOWN or IRREVERSIBLE (NONE when it calls none)"),
    Descriptor(key="@fluss/runtime", type="STRING", description="The executor runtime its source was validated against"),
    _N_ARGS,
    _N_RETURNS,
]


def _keys(descriptors: list[Descriptor]) -> list[str]:
    return [descriptor.key for descriptor in descriptors]


#: What exists on a hub because this service is there: said here, as data, so the hub knows it from
#: the image. ``service.py`` binds each of these to its model and refuses anything not said here.
HOSTS = Hosts(
    structures=[
        Structure(
            identifier="@fluss/workspace",
            label="Workspace",
            description="A workspace: where users design and edit one workflow, holding the saved versions of its graph.",
        ),
        Structure(
            identifier="@fluss/flow",
            label="Flow",
            description="A flow (workflow): one saved, executable version of a workspace's graph of nodes and edges, a pipeline over the hub's actions.",
            descriptors=FLOW_DESCRIPTORS,
        ),
        Structure(
            identifier="@fluss/run",
            label="Run",
            description="A run: one execution of a graph workflow for a rekuest task, with the values, errors and completion it produced.",
            descriptors=[
                Descriptor(key="@fluss/status", type="STRING", description="Where the workflow run stands: RUNNING or COMPLETED"),
            ],
        ),
        Structure(
            identifier="@fluss/pythonflow",
            label="Python Flow",
            description="A Python flow: one immutable version of a workflow written as a Python script instead of a graph, going through DRAFT, PUBLISHED and ARCHIVED.",
            descriptors=PYTHON_FLOW_DESCRIPTORS,
        ),
        Structure(
            identifier="@fluss/pythonrun",
            label="Python Run",
            description="A Python run: one execution of a published Python flow for a rekuest task.",
            descriptors=[
                Descriptor(key="@fluss/status", type="STRING", description="Where the run stands: RUNNING, COMPLETED or FAILED"),
            ],
        ),
    ],
    signals=[
        Signal(
            identifier="@fluss/workspace",
            kinds=["CREATED", "UPDATED", "DELETED"],
            description="A workflow workspace was created, changed or deleted.",
        ),
        Signal(
            identifier="@fluss/flow",
            kinds=["CREATED"],
            descriptors=_keys(FLOW_DESCRIPTORS),
            description="A flow (a saved version of a workspace's workflow graph) was created.",
        ),
        Signal(
            identifier="@fluss/run",
            kinds=["CREATED", "UPDATED", "DELETED"],
            descriptors=["@fluss/status"],
            description="A flow run (a workflow execution) started, changed status (e.g. completed) or was deleted.",
        ),
        Signal(
            identifier="@fluss/pythonflow",
            kinds=["CREATED", "UPDATED", "DELETED"],
            descriptors=_keys(PYTHON_FLOW_DESCRIPTORS),
            description="A Python flow version (a workflow written in Python) was created, published or archived (UPDATED), or a draft deleted.",
        ),
        Signal(
            identifier="@fluss/pythonrun",
            kinds=["CREATED", "UPDATED", "DELETED"],
            descriptors=["@fluss/status"],
            description="A Python flow run (a Python workflow execution) started, finished (COMPLETED/FAILED) or was deleted.",
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
    jobs={
        "ensureadmin": Job(("ensureadmin",), "Create the operator account the config names"),
        "restore_descriptors": Job(("restore_descriptors",), "Store the descriptors of every flow and run that misses one (--all: of every row)"),
    },
    setup=("ensureadmin", "restore_descriptors"),
)

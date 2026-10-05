"""fluss as a service of the hub: what exists here (``arkitekt_service.service``).

Two separate declarations, read by rekuest from the service's manifest (``*service.urls`` in
``urls.py``) and catalogued hub-wide:

* the **structures** fluss hosts, and the descriptors of their objects. The GraphQL types answer
  ``descriptors`` from the same declarations (``reaktion.types``);
* the **signals** it emits: which saves and deletes are announced, with no emit in the mutations.
  Users' triggers are checked against the kinds and descriptor keys declared here.

Hosting announces nothing by itself: a structure with no signal below is hosted silently.

That is all a service is. What can be *done* in this process is not declared here: that is an
agent's to say (``fluss_server.hook_agent``), a different thing with its own configuration.
"""


from reaktion import models
from arkitekt_service.service import Descriptor, Service, organization_of

service = Service("fluss", description="Workflows and their runs.")


# --- Structures: what fluss hosts -----------------------------------------------------

workspace = service.structure(
    models.Workspace,
    "@fluss/workspace",
    description="A workspace: the container users edit the versions of one flow in.",
)
flow = service.structure(
    models.Flow,
    "@fluss/flow",
    descriptors=(
        Descriptor("@fluss/version", "STRING", "Its version label"),
        Descriptor("@fluss/n_nodes", "INT", "How many nodes its graph has"),
        Descriptor("@fluss/n_edges", "INT", "How many edges its graph has"),
        Descriptor("@fluss/brittle", "BOOL", "Whether it fails on any exception"),
    ),
    describe=lambda flow: {
        "@fluss/version": flow.version,
        "@fluss/n_nodes": len(flow.nodes or []),
        "@fluss/n_edges": len(flow.edges or []),
        "@fluss/brittle": bool(flow.brittle),
    },
    description="A flow: one saved, executable version of a workspace's graph of nodes and edges.",
)
run = service.structure(
    models.Run,
    "@fluss/run",
    descriptors=(Descriptor("@fluss/status", "STRING", "Where the run stands: RUNNING or COMPLETED"),),
    describe=lambda run: {"@fluss/status": str(run.status)},
    description="A run: one live execution of a flow for a task.",
)
pythonflow = service.structure(
    models.PythonFlow,
    "@fluss/pythonflow",
    descriptors=(
        Descriptor("@fluss/status", "STRING", "Its lifecycle: DRAFT, PUBLISHED or ARCHIVED"),
        Descriptor("@fluss/physical", "BOOL", "Whether its source may call an action with a PHYSICAL effect"),
    ),
    describe=lambda flow: {"@fluss/status": str(flow.status), "@fluss/physical": flow.is_physical},
    description="A Python flow: one immutable version of a flow written as Python source.",
)
pythonrun = service.structure(
    models.PythonRun,
    "@fluss/pythonrun",
    descriptors=(Descriptor("@fluss/status", "STRING", "Where the run stands: RUNNING, COMPLETED or FAILED"),),
    describe=lambda run: {"@fluss/status": str(run.status)},
    description="A Python run: one execution of a published Python flow for a task.",
)


# --- Signals: what fluss announces -----------------------------------------------------
# A run's status change (RUNNING → COMPLETED) is an UPDATED — the natural thing to trigger on
# ("when a flow finishes, …").

ALL = ("CREATED", "UPDATED", "DELETED")
org = organization_of()
# A run has no organization of its own: it is its flow's.
flow_org = organization_of("flow.organization")

service.model_signal(
    workspace,
    kinds=ALL,
    organization=org,
    description="A workspace was created, changed or deleted.",
)
service.model_signal(
    flow,
    kinds=("CREATED",),
    organization=org,
    description="A flow (a version of a workspace's graph) was created.",
)
service.model_signal(
    run,
    kinds=ALL,
    organization=flow_org,
    description="A flow run started, changed status (e.g. completed) or was deleted.",
)
service.model_signal(
    pythonflow,
    kinds=ALL,
    organization=org,
    description="A Python flow version was created, published or archived (UPDATED), or a draft deleted.",
)
service.model_signal(
    pythonrun,
    kinds=ALL,
    organization=flow_org,
    description="A Python flow run started, finished (COMPLETED/FAILED) or was deleted.",
)

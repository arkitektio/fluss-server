"""fluss as a service of the hub: the models and the code behind what its contract says it hosts.

What exists here (the structures, the descriptors of their objects, the signals and their kinds)
is declared once, as data, in ``fluss_server.contract`` (``hosts``), so that a hub knows it from the
image. This module only binds it: each structure to its model and to what computes its
descriptors, each signal to the saves and deletes that send it. A structure the contract does not
declare cannot be bound, and one it declares that nothing binds here stops the service at its
start. The GraphQL types answer ``descriptors`` from the same binding (``reaktion.types``).

Hosting announces nothing by itself: a structure with no signal below is hosted silently.

That is all a service is. What can be *done* in this process is not declared here: that is an
agent's to say (``fluss_server.hook_agent``), a different thing with its own configuration.
"""


from reaktion import models
from arkitekt_service.service import Service, organization_of

from fluss_server.contract import contract

service = Service("fluss", hosts=contract.description.hosts, description="Workflows and their runs.")


# --- Structures: what fluss hosts -----------------------------------------------------

workspace = service.structure(models.Workspace, "@fluss/workspace")
flow = service.structure(
    models.Flow,
    "@fluss/flow",
    describe=lambda flow: {
        "@fluss/version": flow.version,
        "@fluss/n_nodes": len(flow.nodes or []),
        "@fluss/n_edges": len(flow.edges or []),
        "@fluss/brittle": bool(flow.brittle),
    },
)
run = service.structure(models.Run, "@fluss/run", describe=lambda run: {"@fluss/status": str(run.status)})
pythonflow = service.structure(
    models.PythonFlow,
    "@fluss/pythonflow",
    describe=lambda flow: {"@fluss/status": str(flow.status), "@fluss/physical": flow.is_physical},
)
pythonrun = service.structure(models.PythonRun, "@fluss/pythonrun", describe=lambda run: {"@fluss/status": str(run.status)})


# --- Signals: what fluss announces -----------------------------------------------------
# A run's status change (RUNNING → COMPLETED) is an UPDATED — the natural thing to trigger on
# ("when a flow finishes, …").

org = organization_of()
# A run has no organization of its own: it is its flow's.
flow_org = organization_of("flow.organization")

service.model_signal(workspace, organization=org)
service.model_signal(flow, organization=org)
service.model_signal(run, organization=flow_org)
service.model_signal(pythonflow, organization=org)
service.model_signal(pythonrun, organization=flow_org)

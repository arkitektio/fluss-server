"""fluss as a service of the hub: the models and the code behind what its contract says it hosts.

What exists here (the structures, the descriptors of their objects, the signals and their kinds)
is declared once, as data, in ``fluss_server.contract`` (``hosts``), so that a hub knows it from the
image. This module only binds it: each structure to its model and to what computes its
descriptors, each signal to the saves and deletes that send it. A structure the contract does not
declare cannot be bound, and one it declares that nothing binds here stops the service at its
start. Each described row stores its descriptors on every save (``stored_descriptors``): the
GraphQL types answer ``descriptors`` from there, and a filter's ``requires`` reads it in SQL.

Hosting announces nothing by itself: a structure with no signal below is hosted silently.

That is all a service is. What can be *done* in this process is not declared here: that is an
agent's to say (``fluss_server.hook_agent``), a different thing with its own configuration.
"""


from reaktion import models
from arkitekt_service.service import Service, organization_of
from arkitekt_service.collaborations import items as collaboration_items
from django.db.models.signals import post_save

from fluss_server import descriptors
from fluss_server.contract import contract

service = Service("fluss", hosts=contract.description.hosts, description="Workflows and their runs.")


# --- Collaborations: what an object needs to be seen, put in a collaboration along with it ------------------
# What is part of an object (a run's events and snapshots) is in a collaboration with it by itself.
# These name the rest. A flow's workspace key is nullable, so its flows are not part of it: a
# workspace brings them, and a flow saved into it later (`_flow_saved`).


def _workspace_needs(workspace: models.Workspace) -> list[models.Flow]:
    """A workspace's flows: the versions of its graph."""
    return list(workspace.flows.all())


def _flow_needs(flow: models.Flow) -> list[models.Workspace | None]:
    """The workspace a flow is a version in."""
    return [flow.workspace]


def _run_needs(run: models.Run) -> list[models.Flow | None]:
    """The flow a run executes."""
    return [run.flow]


def _python_run_needs(run: models.PythonRun) -> list[models.PythonFlow]:
    """The Python flow version a run executes."""
    return [run.flow]


# --- Structures: what fluss hosts -----------------------------------------------------

workspace = service.structure(models.Workspace, "@fluss/workspace", depends=_workspace_needs)
flow = service.structure(models.Flow, "@fluss/flow", describe=descriptors.flow_descriptors, depends=_flow_needs)
run = service.structure(models.Run, "@fluss/run", describe=descriptors.run_descriptors, depends=_run_needs)
pythonflow = service.structure(models.PythonFlow, "@fluss/pythonflow", describe=descriptors.python_flow_descriptors)
pythonrun = service.structure(models.PythonRun, "@fluss/pythonrun", describe=descriptors.run_descriptors, depends=_python_run_needs)


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


# A cascading key that points at something shared, not at a whole: a Python run is not part of
# the version it executes (many runs execute one), so sharing a flow shares none of its runs.
service.not_part_of(models.PythonRun, "flow")


def _flow_saved(sender: type[models.Flow], instance: models.Flow, raw: bool = False, **_: object) -> None:
    """A flow saved into a workspace in a collaboration (a new version, by updateWorkspace) comes into that collaboration."""
    if not raw and instance.workspace_id is not None:
        collaboration_items.refresh(instance.workspace)


post_save.connect(_flow_saved, sender=models.Flow, dispatch_uid="fluss-collaborations-flow")

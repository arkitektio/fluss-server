"""fluss as the hub's rekuest sees it: the actions it offers, the signals it emits (vendored ``rekuest_service``).

Like an arkitekt ``App``: one ``Service`` declaration, mounted by ``urls.py`` (``*service.urls``),
read by rekuest from the manifest. Nothing here loops: each run is one pass rekuest started, and
a lost run is followed by the next.
"""

from django.conf import settings

from reaktion import models
from embeddings import engine
from embeddings.healer import reembed_all
from rekuest_service import Service, organization_of

service = Service("fluss", description="Workflows and their runs.")

# The models whose name + description are embedded (see ``embeddings.healer``).
_EMBEDDED_MODELS = (models.Workspace, models.Flow, models.PythonFlow)


# --- Signals ------------------------------------------------------------------------------
# What fluss announces to the hub's rekuest. A run's status change (RUNNING → COMPLETED) is an
# UPDATED — the natural thing to trigger on ("when a flow finishes, …").

service.model_signal(
    models.Flow, "@fluss/flow", kinds=("CREATED",), organization=organization_of(),
    descriptors=lambda flow: {"@fluss/version": flow.version, "@fluss/n_nodes": len(flow.nodes or []), "@fluss/n_edges": len(flow.edges or []), "@fluss/brittle": bool(flow.brittle)},
    descriptor_keys=("@fluss/version", "@fluss/n_nodes", "@fluss/n_edges", "@fluss/brittle"),
    description="A flow (a version of a workspace's graph) was created.",
)
service.model_signal(
    models.Run, "@fluss/run", kinds=("CREATED", "UPDATED", "DELETED"), organization=organization_of("flow.organization"),
    descriptors=lambda run: {"@fluss/status": str(run.status)},
    descriptor_keys=("@fluss/status",),
    description="A flow run started, changed status (e.g. completed) or was deleted.",
)
service.model_signal(
    models.PythonFlow, "@fluss/pythonflow", kinds=("CREATED", "UPDATED", "DELETED"), organization=organization_of(),
    descriptors=lambda flow: {"@fluss/status": str(flow.status), "@fluss/physical": flow.is_physical},
    descriptor_keys=("@fluss/status", "@fluss/physical"),
    description="A Python flow version was created, published or archived (UPDATED), or a draft deleted.",
)
service.model_signal(
    models.PythonRun, "@fluss/pythonrun", kinds=("CREATED", "UPDATED", "DELETED"), organization=organization_of("flow.organization"),
    descriptors=lambda run: {"@fluss/status": str(run.status)},
    descriptor_keys=("@fluss/status",),
    description="A Python flow run started, finished (COMPLETED/FAILED) or was deleted.",
)
service.model_signal(models.Workspace, "@fluss/workspace", kinds=("CREATED", "UPDATED", "DELETED"), organization=organization_of(), description="A workspace was created, changed or deleted.")


@service.action(
    interface="reembed_stale",
    name="Re-embed stale rows",
    description="Re-embed every row whose vector was produced by another embedding model, or by none.",
    # Scheduled only where embeddings are on; ``embeddings.sweep_interval`` is its cadence.
    default_interval=settings.EMBEDDINGS["SWEEP_INTERVAL"] if engine.enabled() else None,
)
def reembed_stale() -> dict:
    """One pass over every embedded model, in row-locked batches (N replicas may run it at once)."""
    return {"reembedded": reembed_all(_EMBEDDED_MODELS, max_batches=50)}

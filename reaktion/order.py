"""GraphQL ordering types for reaktion (one ``order_type`` per model).

Only fields that actually exist on each model are exposed (e.g. Trace has no
``created_at``; ReactiveTemplate has no ``created_at``).
"""

import strawberry_django
from strawberry import auto

from reaktion import models


@strawberry_django.order_type(models.Workspace)
class WorkspaceOrder:
    created_at: auto
    title: auto
    id: auto


@strawberry_django.order_type(models.Flow)
class FlowOrder:
    created_at: auto
    title: auto
    id: auto


@strawberry_django.order_type(models.PythonFlow)
class PythonFlowOrder:
    created_at: auto
    title: auto
    id: auto


@strawberry_django.order_type(models.PythonRun)
class PythonRunOrder:
    created_at: auto
    id: auto


@strawberry_django.order_type(models.ReactiveTemplate)
class ReactiveTemplateOrder:
    title: auto
    id: auto


@strawberry_django.order_type(models.Run)
class RunOrder:
    created_at: auto
    id: auto


@strawberry_django.order_type(models.Snapshot)
class SnapshotOrder:
    created_at: auto
    t: auto
    id: auto


@strawberry_django.order_type(models.RunEvent)
class RunEventOrder:
    created_at: auto
    t: auto
    id: auto


@strawberry_django.order_type(models.Trace)
class TraceOrder:
    id: auto


@strawberry_django.order_type(models.TraceSnapshot)
class TraceSnapshotOrder:
    created_at: auto
    id: auto


@strawberry_django.order_type(models.TraceEvent)
class TraceEventOrder:
    created_at: auto
    id: auto

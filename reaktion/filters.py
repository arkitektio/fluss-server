"""GraphQL filter types for reaktion.

Mirrors mikro's approach: small, prefix-aware filter-field mixins composed into
one ``kante.filter_type`` per model. Prefix awareness lets a filter compose
correctly when nested inside another filter (the ``prefix`` carries the
relation path).
"""

import datetime

import kante
import strawberry
from django.db.models import Q, QuerySet
from embeddings.search import hybrid_search
from kante.types import Info

from reaktion import enums, models


# --- reusable mixins ---------------------------------------------------------


@strawberry.input
class IdsFilterMixin:
    @kante.filter_field(description="Filter by a list of IDs")
    def ids(self, info: Info, value: list[strawberry.ID], prefix: str) -> Q:
        return Q(**{f"{prefix}id__in": value})


@strawberry.input
class TitleSearchFilterMixin:
    @kante.filter_field(description="Search by title (case-insensitive substring)")
    def search(self, info: Info, value: str, prefix: str) -> Q:
        return Q(**{f"{prefix}title__icontains": value})


@strawberry.input
class SemanticTitleSearchFilterMixin:
    """``search`` = substring of the title OR semantic similarity to title + description.

    For the models that carry an embedding (``embeddings.models.EmbeddedDescriptionMixin``:
    Workspace, Flow). Substring hits rank first, then by similarity; nested use (``prefix``)
    stays lexical.
    """

    @kante.filter_field(description="Search by title (case-insensitive substring) or by the meaning of the query against title and description. Substring matches rank first, then by similarity; an explicit `ordering` replaces that ranking")
    def search(self, info: Info, queryset: QuerySet, value: str, prefix: str) -> tuple[QuerySet, Q]:
        """Annotate the distance and OR the semantic predicate onto the substring one."""
        return hybrid_search(queryset, prefix, value, Q(**{f"{prefix}title__icontains": value}))


@strawberry.input
class CreatedAtFilterMixin:
    @kante.filter_field(description="Filter for items created before this datetime")
    def created_before(self, info: Info, value: datetime.datetime, prefix: str) -> Q:
        return Q(**{f"{prefix}created_at__lt": value})

    @kante.filter_field(description="Filter for items created after this datetime")
    def created_after(self, info: Info, value: datetime.datetime, prefix: str) -> Q:
        return Q(**{f"{prefix}created_at__gt": value})


@strawberry.input
class PinnedFilterMixin:
    @kante.filter_field(description="Filter by whether the current user has pinned the item")
    def pinned(self, info: Info, value: bool, prefix: str) -> Q:
        user = info.context.request.user
        if value:
            return Q(**{f"{prefix}pinned_by": user})
        return ~Q(**{f"{prefix}pinned_by": user})


# --- per-model filter types --------------------------------------------------


@kante.filter_type(models.Workspace)
class WorkspaceFilter(IdsFilterMixin, SemanticTitleSearchFilterMixin, CreatedAtFilterMixin, PinnedFilterMixin):
    pass


@kante.filter_type(models.Flow)
class FlowFilter(IdsFilterMixin, SemanticTitleSearchFilterMixin, CreatedAtFilterMixin, PinnedFilterMixin):
    pass


@kante.filter_type(models.ReactiveTemplate)
class ReactiveTemplateFilter(IdsFilterMixin, TitleSearchFilterMixin):
    @kante.filter_field(description="Filter by reactive implementation")
    def implementations(self, info: Info, value: list[enums.ReactiveImplementation], prefix: str) -> Q:
        return Q(**{f"{prefix}implementation__in": value})


@kante.filter_type(models.Run)
class RunFilter(IdsFilterMixin, CreatedAtFilterMixin, PinnedFilterMixin):
    @kante.filter_field(description="Search by task id (case-insensitive substring)")
    def search(self, info: Info, value: str, prefix: str) -> Q:
        return Q(**{f"{prefix}task_id__icontains": value})


@kante.filter_type(models.Snapshot)
class SnapshotFilter(IdsFilterMixin, CreatedAtFilterMixin):
    pass


@kante.filter_type(models.RunEvent)
class RunEventFilter(IdsFilterMixin, CreatedAtFilterMixin):
    @kante.filter_field(description="Filter by event kind")
    def kinds(self, info: Info, value: list[enums.RunEventKind], prefix: str) -> Q:
        return Q(**{f"{prefix}kind__in": value})


@kante.filter_type(models.Trace)
class TraceFilter(IdsFilterMixin, PinnedFilterMixin):
    pass


@kante.filter_type(models.TraceSnapshot)
class TraceSnapshotFilter(IdsFilterMixin, CreatedAtFilterMixin):
    pass


@kante.filter_type(models.TraceEvent)
class TraceEventFilter(IdsFilterMixin, CreatedAtFilterMixin):
    pass

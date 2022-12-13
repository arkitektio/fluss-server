import django_filters
from flow.models import Workspace, Flow, Run


class WorkspaceFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Search for substring of name"
    )
    search = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Search for substring of name"
    )


class ReactiveTemplateFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Search for substring of name"
    )


class FlowFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="workspace__name",
        lookup_expr="icontains",
        label="Search for substring of name",
    )
    workspace = django_filters.ModelChoiceFilter(
        queryset=Workspace.objects.all(), field_name="diagram"
    )


class RunFilter(django_filters.FilterSet):
    flow = django_filters.ModelChoiceFilter(
        queryset=Flow.objects.all(), field_name="flow"
    )


class RunLogFilter(django_filters.FilterSet):
    run = django_filters.ModelChoiceFilter(queryset=Run.objects.all(), field_name="run")


class SnapshotFilter(django_filters.FilterSet):
    run = django_filters.ModelChoiceFilter(queryset=Run.objects.all(), field_name="run")

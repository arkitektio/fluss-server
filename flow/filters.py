import django_filters
from flow.models import Flow, Run


class FlowFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Search for substring of name"
    )


class RunFilter(django_filters.FilterSet):
    flow = django_filters.ModelChoiceFilter(
        queryset=Flow.objects.all(), field_name="flow"
    )


class RunLogFilter(django_filters.FilterSet):
    run = django_filters.ModelChoiceFilter(queryset=Run.objects.all(), field_name="run")


class SnapshotFilter(django_filters.FilterSet):
    run = django_filters.ModelChoiceFilter(queryset=Run.objects.all(), field_name="run")

import django_filters
from flow.models import Workspace, Flow, Run, Condition
import graphene
from django import forms
from graphene_django.forms.converter import convert_form_field


class IDChoiceField(forms.JSONField):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def overwritten_type(self, **kwargs):
        return graphene.List(graphene.ID, **kwargs)


@convert_form_field.register(IDChoiceField)
def convert_form_field_to_string_list(field):
    return field.overwritten_type(required=field.required)


class IDChoiceFilter(django_filters.MultipleChoiceFilter):
    field_class = IDChoiceField

    def __init__(self, *args, **kwargs):


        super().__init__(*args, **kwargs, field_name="pk")

class MultiStringField(forms.TypedMultipleChoiceField):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def overwritten_type(self, **kwargs):
        return graphene.List(graphene.String, **kwargs)
    

@convert_form_field.register(MultiStringField)
def convert_form_field_to_string_list(field):
    return field.overwritten_type(required=field.required)
    
class MultiStringFilter(django_filters.MultipleChoiceFilter):
    field_class = MultiStringField

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class PinnedFilterMixin(django_filters.FilterSet):
    pinned = django_filters.BooleanFilter(
        method="my_pinned_filter", label="Filter by pinned"
    )

    def my_pinned_filter(self, queryset, name, value):
        if value:
            if (
                self.request
                and self.request.user
                and self.request.user.is_authenticated
            ):
                # needs to be checked becaust request is not ensured to be set
                return queryset.filter(pinned_by=self.request.user)
            else:
                raise Exception("Pin can only be used by authenticated users")
        else:
            return queryset
        
class TimeFilterMixin(django_filters.FilterSet):
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )
    created_at = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )
    created_day = django_filters.DateTimeFilter(
        field_name="created_at", method="my_created_day_filter"
    )
    created_while = MultiStringFilter(
        field_name="created_while", method="my_created_while_filter"
    )
    order = django_filters.OrderingFilter(fields={"created_at": "time"})

    def my_created_day_filter(self, queryset, name, value):
        return queryset.filter(
            created_at__date__year=value.year,
            created_at__date__month=value.month,
            created_at__date__day=value.day,
        )
    
    def my_created_while_filter(self, queryset, name, value):
        return queryset.filter(
            created_while__in=value
        )


class IdsFilter(django_filters.FilterSet):

    ids = IDChoiceFilter(label="Filter by values")

    def my_values_filter(self, queryset, name, value):
        if value:
            return queryset.filter(id__in=value)
        else:
            return queryset
class WorkspaceFilter(IdsFilter,  TimeFilterMixin, PinnedFilterMixin,django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Search for substring of name"
    )
    search = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Search for substring of name"
    )


class ReactiveTemplateFilter(IdsFilter, django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Search for substring of name"
    )


class FlowFilter(IdsFilter, TimeFilterMixin, PinnedFilterMixin, django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="workspace__name",
        lookup_expr="icontains",
        label="Search for substring of name",
    )
    workspace = django_filters.ModelChoiceFilter(
        queryset=Workspace.objects.all(), field_name="workspace"
    )


class RunFilter(IdsFilter,TimeFilterMixin, PinnedFilterMixin, django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="flow__workspace__name",
        lookup_expr="icontains",
        label="Search for substring of name",
    )


class RunLogFilter(IdsFilter, django_filters.FilterSet):
    run = django_filters.ModelChoiceFilter(queryset=Run.objects.all(), field_name="run")


class SnapshotFilter(IdsFilter, django_filters.FilterSet):
    run = django_filters.ModelChoiceFilter(queryset=Run.objects.all(), field_name="run")


class ConditionFilter(IdsFilter, TimeFilterMixin, PinnedFilterMixin, django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="flow__workspace__name",
        lookup_expr="icontains",
        label="Search for substring of name",
    )



class ConditionSnapshotFilter(IdsFilter, django_filters.FilterSet):
    condition = django_filters.ModelChoiceFilter(queryset=Condition.objects.all(), field_name="condition")
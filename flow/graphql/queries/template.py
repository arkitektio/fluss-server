from balder.types.mutation.base import BalderMutation
from balder.types import BalderQuery
import graphene
from flow import models, types, filters
from lok import bounced


class ReactiveTemplate(BalderQuery):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def resolve(root, info, id=None):
        graph = models.ReactiveTemplate.objects.get(id=id)
        return graph

    class Meta:
        type = types.ReactiveTemplate
        operation = "reactivetemplate"


class ReactiveNodes(BalderQuery):
    class Meta:
        type = types.ReactiveTemplate
        list = True
        filter = filters.ReactiveTemplateFilter
        operation = "reactivetemplates"

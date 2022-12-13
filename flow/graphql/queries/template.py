from balder.types.mutation.base import BalderMutation
from balder.types import BalderQuery
import graphene
from flow import models, types, filters
from lok import bounced
from flow.inputs import ReactiveImplementation

class ReactiveTemplate(BalderQuery):
    class Arguments:
        id = graphene.ID(required=False, description="The Id of the Graph")
        implementation = graphene.Argument(ReactiveImplementation, required=False)

    @bounced(anonymous=False)
    def resolve(root, info, id=None, implementation=None):
        if id:
            return models.ReactiveTemplate.objects.get(id=id)
        if implementation:
            return models.ReactiveTemplate.objects.get(implementation=implementation)

    class Meta:
        type = types.ReactiveTemplate
        operation = "reactivetemplate"


class ReactiveNodes(BalderQuery):
    class Meta:
        type = types.ReactiveTemplate
        list = True
        filter = filters.ReactiveTemplateFilter
        operation = "reactivetemplates"

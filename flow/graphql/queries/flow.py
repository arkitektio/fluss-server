from balder.types.mutation.base import BalderMutation
from balder.types import BalderQuery
import graphene
from flow import models, types, filters
from lok import bounced


class Workspace(BalderQuery):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    def resolve(root, info, id=None):
        graph = models.Workspace.objects.get(id=id)
        return graph

    class Meta:
        type = types.Workspace
        operation = "workspace"


class Workspaces(BalderQuery):
    class Meta:
        type = types.Workspace
        list = True
        paginate = True
        filter = filters.WorkspaceFilter
        operation = "workspaces"


class Flows(BalderQuery):
    class Meta:
        type = types.Flow
        list = True
        paginate = True
        filter = filters.FlowFilter
        operation = "flows"

class MyFlows(BalderQuery):
    class Meta:
        type = types.Flow
        list = True
        paginate = True
        personal = "created_by"
        filter = filters.FlowFilter
        operation = "myflows"



class FlowDetail(BalderQuery):
    class Arguments:
        id = graphene.ID(description="A unique ID for this Graph")

    def resolve(root, info, *args, id=None, template=None, node=None):
        return models.Flow.objects.get(id=id)

    class Meta:
        type = types.Flow
        operation = "flow"


class MyWorkspaces(BalderQuery):
    class Meta:
        list = True
        personal = "creator"
        filter = filters.WorkspaceFilter
        paginate = True
        type = types.Workspace
        operation = "myworkspaces"

from email.policy import default
import json
from balder.types import BalderMutation
import graphene
from flow import models, types
from lok import bounced
import logging
from flow.inputs import GraphInput, NodeInput, EdgeInput
from graphene.types.generic import GenericScalar
from balder.types.scalars import ImageFile
import namegenerator
import hashlib
from flow.utils import fill_created
logger = logging.getLogger(__name__)


def graph_hash(graph_hash) -> str:
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    # We need to sort arguments so {'a': 1, 'b': 2} is
    # the same as {'b': 2, 'a': 1}
    encoded = json.dumps(graph_hash, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()


class UpdateWorkspace(BalderMutation):
    class Arguments:
        id = graphene.ID(required=True)
        graph = graphene.Argument(GraphInput, required=False)
        brittle = graphene.Boolean(default_value=False)
        screenshot = ImageFile(required=False)

    @bounced(anonymous=False)
    def mutate(root, info, id, graph=None, brittle=False, screenshot=None):

        workspace = models.Workspace.objects.get(id=id)

        flow, cr = models.Flow.objects.get_or_create(
            workspace=workspace,
            restrict=workspace.restrict,
            hash=graph_hash(graph),
            defaults={"graph": graph, "brittle": brittle},
            **fill_created(info)
        )

        flow.brittle = brittle or flow.brittle
        flow.screenshot = screenshot or flow.screenshot
        flow.save()

        return workspace

    class Meta:
        type = types.Workspace
        operation = "updateworkspace"


class ImportFlow(BalderMutation):
    class Arguments:
        name = graphene.String(required=False)
        graph = graphene.Argument(GraphInput, required=False)

    @bounced(anonymous=False)
    def mutate(root, info, name, graph=None, brittle=False):

        workspace = models.Workspace.objects.create(name=name)

        flow, cr = models.Flow.objects.get_or_create(
            workspace=workspace,
            hash=graph_hash(graph),
            defaults={"graph": graph, "brittle": brittle, **fill_created(info)},

        )

        flow.save()

        return workspace

    class Meta:
        type = types.Workspace
        operation = "importflow"



class DrawVanilla(BalderMutation):
    class Arguments:
        name = graphene.String(required=False)
        brittle = graphene.Boolean(default_value=False)
        restrict = graphene.List(graphene.String, required=False, description="Do you want to restrict nodes to specific apps?")

    @bounced(anonymous=False)
    def mutate(
        root,
        info,
        name=None,
        brittle=False,
        restrict=None,
    ):

        x = name or namegenerator.gen()

        nodes = [
            {
                "id": "1",
                "typename": "ArgNode",
                "instream": [[]],
                "outstream": [[]],
                "constream": [[]],
                "position": {"x": 0, "y": 50},
            },
            {
                "id": "2",
                "typename": "ReturnNode",
                "instream": [[]],
                "outstream": [[]],
                "constream": [[]],
                "position": {"x": 1500, "y": 50},
            },
            {
                "id": "3",
                "typename": "KwargNode",
                "instream": [[]],
                "outstream": [[]],
                "constream": [[]],
                "position": {"x": 750, "y": 400},
            },
        ]

        graph = {
            "nodes": nodes,
            "edges": [],
            "globals": [],
            "args": [],
            "kwargs": [],
            "returns": [],
        }

        workspace = models.Workspace.objects.create(name=x, creator=info.context.user, restrict=restrict or [])

        flow = models.Flow.objects.create(
            restrict=restrict or [],
            workspace=workspace,
            graph=graph,
            hash=graph_hash(graph),
            name=name,
            creator=info.context.user,
            brittle=brittle or False,
            **fill_created(info)
        )
        return workspace

    class Meta:
        type = types.Workspace
        operation = "drawvanilla"


class DeleteFlowReturn(graphene.ObjectType):
    id = graphene.ID()


class DeleteFlow(BalderMutation):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def mutate(root, info, id=None):

        graph = models.Flow.objects.get(id=id)
        graph.delete()
        return {"id": id}

    class Meta:
        type = DeleteFlowReturn


class DeleteWorkspaceReturn(graphene.ObjectType):
    id = graphene.ID()


class DeleteWorkspace(BalderMutation):
    class Arguments:
        id = graphene.ID(required=True, description="The Id of the Graph")

    @bounced(anonymous=False)
    def mutate(root, info, id=None):

        graph = models.Workspace.objects.get(id=id)
        graph.delete()
        return {"id": id}

    class Meta:
        type = DeleteWorkspaceReturn


class PinFlow(BalderMutation):
    """Pin Run
    
    This mutation pins an Runs and returns the pinned Run."""

    class Arguments:
        id = graphene.ID(required=True, description="The ID of the representation")
        pin = graphene.Boolean(required=True, description="The pin state")

    @bounced()
    def mutate(root, info, id, pin, **kwargs):
        rep = models.Flow.objects.get(id=id)
        if pin:
            rep.pinned_by.add(info.context.user)
        else:
            rep.pinned_by.remove(info.context.user)
        rep.save()
        return rep

    class Meta:
        type = types.Flow


class PinWorkspace(BalderMutation):
    """Pin Run
    
    This mutation pins an Runs and returns the pinned Run."""

    class Arguments:
        id = graphene.ID(required=True, description="The ID of the representation")
        pin = graphene.Boolean(required=True, description="The pin state")

    @bounced()
    def mutate(root, info, id, pin, **kwargs):
        rep = models.Workspace.objects.get(id=id)
        if pin:
            rep.pinned_by.add(info.context.user)
        else:
            rep.pinned_by.remove(info.context.user)
        rep.save()
        return rep

    class Meta:
        type = types.Workspace
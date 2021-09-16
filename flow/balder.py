import logging

import graphene
from graphene.types.generic import GenericScalar
from herre.auth import HerreClient
from lok import bounced

from balder.types import BalderMutation, BalderQuery
from flow import models, types
from flow.diagram import (ArgData, ArgNode,ArkitektNode,
                          ArkitektType, Diagram, KwargData, KwargNode, Node,
                          ReturnData, ReturnNode)
from flow.graphql.mutations import *
from flow.graphql.queries import *

logger = logging.getLogger(__name__)

from arkitekt import Node as ApiNode
from arkitekt.schema.node import NodeType
from arkitekt.schema.template import Template as ApiTemplate
import asyncio


herre = HerreClient()





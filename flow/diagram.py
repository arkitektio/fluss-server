from typing import List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

class Edge(BaseModel):
    type: str
    source: str
    target: str
    sourceHandle: str
    targetHandle: str


class ArkitektType(str, Enum):
    FUNCTION = "FUNCTION"
    GENERATOR = "GENERATOR"


class Arkitekt(BaseModel):
    id: str
    args: list
    kwargs: list
    returns: list
    type: ArkitektType



class Selector(BaseModel):
    provider: Optional[List[str]]



class ArkitektData(BaseModel):
    node: Arkitekt
    selector: Selector


class Port(BaseModel):
    type: str = Field(None, alias='__typename')
    description: Optional[str]
    key: str
    label: Optional[str]


class ArgPort(Port):
    identifier: Optional[str]
    widget: Optional[dict]


class KwargPort(Port):
    identifier: Optional[str]
    default: Optional[Union[str, int, dict]]


class ReturnPort(Port):
    identifier: Optional[str]

class ArgData(BaseModel):
    args: List[ArgPort]

class KwargData(BaseModel):
    kwargs: List[KwargPort]

class ReturnData(BaseModel):
    returns: List[ReturnPort]

class Node(BaseModel):
    type: str
    position: dict
    data: Union[ArkitektData, ArgData, KwargData, ReturnData]


class Diagram(BaseModel):
    elements: List[Union[Node, Edge]]
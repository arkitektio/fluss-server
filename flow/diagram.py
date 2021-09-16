from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import ForwardRef

ArgPort = ForwardRef("ArgPort")
KwargPort = ForwardRef("KwargPort")
ReturnPort = ForwardRef("ReturnPort")

class Constants(dict):
    pass

class ArkitektType(str, Enum):
    FUNCTION = "FUNCTION"
    GENERATOR = "GENERATOR"


class Arkitekt(BaseModel):
    id: str
    name: str
    args: list
    kwargs: list
    returns: list
    type: ArkitektType


class Selector(BaseModel):
    providers: Optional[List[str]]
    templates: Optional[List[str]]


class ArkitektData(BaseModel):
    node: Arkitekt
    selector: Selector

class Widget(BaseModel):
    type: str = Field(None, alias='__typename')
    query:  Optional[str]
    dependencies: Optional[List[str]]
    max:  Optional[str]
    min:  Optional[str]


class Port(BaseModel):
    type: Optional[str] = Field(None, alias='__typename')
    description: Optional[str]
    key: Optional[str]
    label: Optional[str]


class ArgPort(Port):
    identifier: Optional[str]
    widget: Optional[Widget]
    child: Optional[ArgPort]


class KwargPort(Port):
    identifier: Optional[str]
    default: Optional[Union[str, int, dict]]
    child: Optional[KwargPort]


class ReturnPort(Port):
    identifier: Optional[str]
    child: Optional[ReturnPort]

class ArgData(BaseModel):
    args: List[ArgPort]

class KwargData(BaseModel):
    kwargs: List[KwargPort]

class ReturnData(BaseModel):
    returns: List[ReturnPort]


class Edge(BaseModel):
    id: str
    type: str
    label: Optional[str]
    style: Optional[dict]
    source: str
    target: str
    sourceHandle: str
    targetHandle: str


class Position(BaseModel):
    x: int
    y: int


class Node(BaseModel):
    id: str
    type: str
    position: Optional[Position]
    data: Union[ArkitektData, ArgData, KwargData, ReturnData]

    @validator('type')
    def type_match(cls, v):
        if v == cls._type: return v
        raise ValueError("Is not the Right")


class ArkitektNode(Node):
    _type = "arkitektNode"
    data: ArkitektData



class ArgNode(Node):
    _type = "argNode"
    data: ArgData


class KwargNode(Node):
    _type = "kwargNode"
    data: KwargData


class ReturnNode(Node):
    _type = "returnNode"
    data: ReturnData


class Diagram(BaseModel):
    zoom: Optional[float]
    position: Optional[List[int]]
    elements: List[Union[ArkitektNode, ArgNode, KwargNode, ReturnNode, Edge]]


ArgPort.update_forward_refs()
KwargPort.update_forward_refs()
ReturnPort.update_forward_refs()
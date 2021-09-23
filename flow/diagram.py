from typing import Any, List, Optional, Union
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
    typename: str = Field(None, alias='__typename')
    query:  Optional[str]
    dependencies: Optional[List[str]]
    max:  Optional[str]
    min:  Optional[str]


class Port(BaseModel):
    typename: Optional[str] = Field(None, alias='__typename')
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
        raise ValueError(f"Is not the Right Type {v}. Would Expect {cls._type}")


class ArkitektNode(Node):
    data: ArkitektData

class ArkitektFuncNode(ArkitektNode):
    _type = "arkitektFuncNode"

class ArkitektGenNode(ArkitektNode):
    _type = "arkitektGenNode"

class CombinationData(BaseModel):
    arg1: List[Port]
    arg2: List[Port]
    return1: List[Port]


class ReactiveNode(Node):
    pass

class CombinatorNode(ReactiveNode):
    data: CombinationData

class ZipNode(CombinatorNode):
    _type = "zipNode"

class MergeNode(CombinatorNode):
    _type = "mergeNode"

class WithLatestFromNode(CombinatorNode):
    _type = "withLatestFromNode"

class CombineLatestNode(CombinatorNode):
    _type = "combineLatestNode"

class IONode(Node):
    pass

class ArgNode(IONode):
    _type = "argNode"
    data: ArgData


class KwargNode(IONode):
    _type = "kwargNode"
    data: KwargData


class ReturnNode(IONode):
    _type = "returnNode"
    data: ReturnData


DiagramNode = Union[ArkitektFuncNode, ArkitektGenNode, ArgNode, KwargNode, ZipNode, MergeNode, WithLatestFromNode, ReturnNode, Edge]



class Diagram(BaseModel):
    zoom: Optional[float]
    position: Optional[List[int]]
    elements: List[DiagramNode]


ArgPort.update_forward_refs()
KwargPort.update_forward_refs()
ReturnPort.update_forward_refs()
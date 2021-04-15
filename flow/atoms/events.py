from typing import Any
from pydantic import BaseModel


class PortEvent(BaseModel):
    handle: str


class PassInEvent(PortEvent):
    value: Any

class PassOutEvent(PortEvent):
    node_id: str
    value: Any

class DoneInEvent(PortEvent):
    pass
    
class DoneOutEvent(PortEvent):
    node_id: str
    pass
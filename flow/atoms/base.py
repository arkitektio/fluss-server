from .events import *
from ..diagram import Node
from abc import ABC, abstractmethod
import asyncio
from bergen.console import console


class Atom(ABC):

    def __init__(self, actionQueue: asyncio.Queue, node: Node) -> None:
        self.action_queue = actionQueue
        self.node = node
        self.run_task = None
        pass

    async def log(self, message):
        console.log(message)

    async def on_except(self, exception):
        console.print_exception()
    
    @abstractmethod
    async def on_event(self, event: PortEvent):
        raise NotImplementedError("Needs to be implemented")

    async def send_pass(self, handle, return_or_yield):
        await self.action_queue.put(PassOutEvent(node_id=self.node.id, handle=handle, value=return_or_yield))

    async def send_done(self, handle):
        await self.action_queue.put(DoneOutEvent(node_id=self.node.id, handle=handle))

    async def start(self):
        self.run_task = asyncio.create_task(self.run())

    async def cancel(self):
        self.run_task.cancel()
        
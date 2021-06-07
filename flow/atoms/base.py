from bergen.handlers.assign import AssignHandler
from bergen.messages.postman.log import LogLevel
from .events import *
from ..diagram import Node
from abc import ABC, abstractmethod
import asyncio
from bergen.console import console


class Atom(ABC):

    def __init__(self, actionQueue: asyncio.Queue, node: Node, assign_handler: AssignHandler) -> None:
        self.action_queue = actionQueue
        self.node = node
        self.run_task = None
        self.assign_handler = assign_handler
        pass

    async def log(self, message, level=LogLevel.INFO):
        await self.assign_handler.log(f"Node {self.node.id}: {message}", level=level)

    async def on_except(self, exception):
        console.print_exception()
        await self.assign_handler.log(exception)
    
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
        console.log("Atom here is being cancelled")
        self.run_task.cancel()
        try:
            await self.run_task
        except asyncio.CancelledError:
            print("Cancellation finished")
        
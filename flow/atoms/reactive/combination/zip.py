import asyncio
from flow.atoms.base import Atom
from flow.atoms.events import *
from flow.diagram import Node

class ZipAtom(Atom):


    def __init__(self, actionQueue: asyncio.Queue,  node: Node) -> None:
        super().__init__(actionQueue, node)
        self.arg_one_queue = asyncio.Queue()
        self.arg_two_queue = asyncio.Queue()

        self.arg_one_active = True
        self.arg_two_active = True
        self.run_task = None

    async def on_event(self, event: PortEvent):
        if isinstance(event, PassInEvent):
            if event.handle == "arg1": await self.arg_one_queue.put(event.value)
            elif event.handle == "arg2": await self.arg_two_queue.put(event.value)
        if isinstance(event, DoneInEvent):
            if event.handle == "arg1": self.arg_one_active = False
            if event.handle == "arg2": self.arg_two_active = False
            if not self.arg_two_active and not self.arg_one_active:
                self.cancel()
                await self.send_done()


    async def run(self):
        while True:
            returns = await asyncio.gather(self.arg_one_queue.get(), self.arg_two_queue.get())
            await self.send_pass("returns", returns)



from abc import abstractmethod
import asyncio
from bergen.contracts.reservation import Reservation
from flow.atoms.base import Atom
from flow.atoms.events import *
from flow.diagram import Node, Constants

class ArkitektAtom(Atom):

    def __init__(self, actionQueue: asyncio.Queue,  node: Node , res: Reservation, constants: Constants) -> None:
        super().__init__(actionQueue, node)
        self.arg_queue = asyncio.Queue()
        self.contants = constants
        self.res = res
        self.run_task = None

    async def on_event(self, event: PortEvent):
        if event.handle == "args": await self.arg_queue.put(event)

    async def push(self, return_or_yield):
        await self.send_pass("returns", return_or_yield)

    async def done(self):
        await self.send_done("returns")

    @abstractmethod
    async def run(self):
        raise NotImplementedError("Overwrite")



class FunctionalArkitektAtom(ArkitektAtom):

    async def run(self):
        try:
            while True:
                event = await self.arg_queue.get()
                if isinstance(event, DoneInEvent):
                    # We are done, just let us send this further, 
                    await self.log(f"[green] We are done. Shutting Down!")
                    await self.done()
                    break

                if isinstance(event, PassInEvent):
                    ' we will never break a current thing as long as it is not cancelled'
                    await self.log(f"[blue]Calling Node {self.node.data.node.name} as Func")
                    #returns = await self.res.assign(*args, **self.contants)
                    returns = await self.res.assign(*event.value, **self.contants)
                    await self.log(f"Pushing {returns}")
                    await self.push(returns)
        except Exception as e:
            await self.on_except(e)


class GenerativeArkitektAtom(ArkitektAtom):

    def __init__(self, actionQueue: asyncio.Queue, node: Node, res: Reservation, constants: Constants) -> None:
         super().__init__(actionQueue, node, res, constants)
         self.left_is_done = False

    async def on_event(self, event: PortEvent):

        if isinstance(event, PassInEvent):
            assert event.handle == "args", "Assigned different port"
            await self.arg_queue.put(event)
        if isinstance(event, DoneInEvent):
            assert event.handle == "args", "Assigned different port"
            self.left_is_done = True   


    async def run(self):
        try:
            while True:
                event = await self.arg_queue.get()
                await self.log(f"Calling Node {self.node.data.node.name} as Gen {event.value}")

                async for yields in self.res.stream(*event.value, **self.contants):
                    await self.log(f"Yielding {yields}")
                    await self.push(yields)

                await self.log("[yellow] oINOINOINOINOINOIN")

                if self.left_is_done:
                    # if every input is done and we are done, well we are really done
                    await self.done()
                    break
                
        except Exception as e:
            await self.on_except(e)

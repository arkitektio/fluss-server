


from abc import abstractmethod
import asyncio
from bergen.contracts.reservation import Reservation
from bergen.handlers.assign import AssignHandler
from bergen.messages.postman.progress import ProgressLevel
from flow.atoms.base import Atom
from flow.atoms.events import *
from flow.diagram import Node, Constants

class ArkitektAtom(Atom):

    def __init__(self, actionQueue: asyncio.Queue,  node: Node , res: Reservation, constants: Constants, assign_handler: AssignHandler) -> None:
        super().__init__(actionQueue, node, assign_handler)
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
                    await self.log(f"We are done. Shutting Down!", level=ProgressLevel.DEBUG)
                    await self.done()
                    break

                if isinstance(event, PassInEvent):
                    ' we will never break a current thing as long as it is not cancelled'
                    await self.log(f"Calling as Func", level=ProgressLevel.DEBUG)
                    #returns = await self.res.assign(*args, **self.contants)
                    args = event.value if isinstance(event.value, list) else [event.value]
                    returns = await self.res.assign(*args, **self.contants, bypass_shrink=True, bypass_expand=True)
                    await self.log(f"Pushing {returns}", level=ProgressLevel.DEBUG)
                    await self.push(returns)
        except Exception as e:
            await self.on_except(e)


class GenerativeArkitektAtom(ArkitektAtom):

    def __init__(self, actionQueue: asyncio.Queue, node: Node, res: Reservation, constants: Constants, assign_handler: AssignHandler) -> None:
         super().__init__(actionQueue, node, res, constants, assign_handler)
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
                await self.log(f"Calling Node {self.node.data.node.name} as Gen {event.value}", level=ProgressLevel.DEBUG)

                args = event.value if isinstance(event.value, list) else [event.value]
                async for yields in self.res.stream(*args, **self.contants, bypass_shrink=True, bypass_expand=True):
                    await self.log(f"Yielding {yields}", level=ProgressLevel.INFO)
                    await self.push(yields)


                if self.left_is_done:
                    # if every input is done and we are done, well we are really done
                    await self.done()
                    break
                
        except Exception as e:
            await self.on_except(e)

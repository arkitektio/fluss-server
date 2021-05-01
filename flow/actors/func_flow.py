from bergen.messages.postman.progress import ProgressLevel
from flow.utils import get_diagram_for_arkitekt_template_id
from bergen.handlers.assign import AssignHandler
from bergen.handlers.unreserve import UnreserveHandler
from bergen.handlers.reserve import ReserveHandler
from bergen.handlers.provide import ProvideHandler
from flow.atoms.arkitekt import FunctionalArkitektAtom, GenerativeArkitektAtom
from flow.atoms.base import Atom
from flow.parser import Parser
from bergen.debugging import DebugLevel
from typing import Dict, List, Tuple, Union
from bergen.actors.classic import ClassicFuncActor, ClassicGenActor
from bergen.messages import *
from bergen.models import Node
from bergen.schema import NodeType
from flow.atoms.events import *
from flow import diagram
import asyncio
from bergen.console import console
from bergen.contracts import Reservation





class FuncFlowActor(ClassicFuncActor):
    expandInputs = False
    shrinkOutputs = False
    """ Flow Base receives a Pod with an attached template """

    async def on_provide(self, provide: ProvideHandler):
        # graph = await Graph.asyncs.get(template=self.pod.template)
        self.diagram: diagram.Diagram = await get_diagram_for_arkitekt_template_id(provide.template_id)
        
        self.nodes =  [ node for node in self.diagram.elements if isinstance(node, diagram.Node)]

        self.edges = [ edge for edge in self.diagram.elements if isinstance(edge, diagram.Edge)]
    
        self.argNode = next((node for node in  self.nodes if isinstance(node, diagram.ArgNode)), None) # We only want the first one
        self.kwargNode = next((node for node in  self.nodes if isinstance(node, diagram.KwargNode)), None) # We only want the first one
        self.returnNode = next((node for node in  self.nodes if isinstance(node, diagram.ReturnNode)), None) # We only want the first one

        self.arkitektNodes = [node for node in  self.nodes if isinstance(node, diagram.ArkitektNode)]

        self.gen_nodes = [node for node in self.arkitektNodes if node.type == NodeType.GENERATOR]
        assert len(self.gen_nodes) == 0, "We cannot have Generator Nodes in a Functional Flow so far, this is a configuration Error"

        await provide.log(self.argNode, level=ProgressLevel.INFO)
        await provide.log(self.kwargNode, level=ProgressLevel.INFO)
        await provide.log(self.returnNode, level=ProgressLevel.INFO)
        
        await provide.log(f"Querying ArkitektNodes {self.arkitektNodes}", level=ProgressLevel.INFO)
        self.nodeIDs = [node.id for node in self.arkitektNodes]
        self.nodeSelectors = [node.data.selector for node in self.arkitektNodes]
        nodeInstanceFutures = [Node.asyncs.get(id=node.data.node.id)for node in self.arkitektNodes]
        self.nodeInstances = await asyncio.gather(*nodeInstanceFutures)

        self.parser = Parser(self.diagram)


    async def on_reserve(self, handler: ReserveHandler) -> None:
        await handler.log("Workflow: Running on a Functional Flow Handler", level=ProgressLevel.DEBUG)
        await handler.log("Workflow: Reserving Arkitekt nodes", level=ProgressLevel.INFO)
        console.log(f"[blue] {self.nodeSelectors}")
        reservationsContexts = [node.reserve(**selector.dict(), bounced=handler.bounced) for node, selector in zip(self.nodeInstances, self.nodeSelectors)]
        reservationEnterFutures = [res.start() for res in reservationsContexts]
        reservations = await asyncio.gather(*reservationEnterFutures)

        await handler.log("Workflow: Building a Reservation map", level=ProgressLevel.DEBUG)
        return { node_id: reservation for node_id, reservation in zip(self.nodeIDs, reservations)}


    async def assign(self, assign_handler: AssignHandler, reserve_handler: ReserveHandler, args, kwargs):

        assert len(self.argNode.data.args) == len(args), "Received different arguments then our ArgNode requires"

        reservations: Dict[str, Reservation] = reserve_handler.context

        action_queue = asyncio.Queue()

        self.nodeIDConstantsMap: Dict[str, diagram.Constants] = {}

        for kwarg, value  in kwargs.items():
            for kwarg_handle, node in self.parser.connectedNodesWithHandle(self.kwargNode.id, f"kwarg_{kwarg}"):
                kwarg = kwarg_handle[len("kwarg_"):]
                self.nodeIDConstantsMap.setdefault(node.id, {})[kwarg] = value


        await assign_handler.log("Workflow: Building a Reservation map", level=ProgressLevel.DEBUG)

        runs: List[Tuple[str, Atom]] = []

        await assign_handler.log("Workflow: Instantiating Node Runs: Creating All necessary Queues for our Eventbus",level=ProgressLevel.DEBUG)
        for node in self.nodes:
            if isinstance(node, diagram.ArkitektNode):
                res = reservations[node.id]
                constants = self.nodeIDConstantsMap.get(node.id, {})
                if node.data.node.type == NodeType.GENERATOR:
                    runs.append((node.id, GenerativeArkitektAtom(action_queue, node, res, constants, assign_handler)))
                if node.data.node.type == NodeType.FUNCTION:
                    runs.append((node.id, FunctionalArkitektAtom(action_queue, node, res, constants, assign_handler)))


        tasks = []
        await assign_handler.log("Workflow: Creating Runs as tasks",level=ProgressLevel.DEBUG)
        for id, run in runs:
            tasks.append((id, await run.start()))


        nodeIDRunMap = {id: run for id, run in runs}
        nodeIDTaskMap = {id: task for id, task in tasks}

        await assign_handler.log(nodeIDRunMap)
        # We send our first arguments 

        initial_nodes = self.parser.getInitialNodes()


        await assign_handler.log(f"Workflow: Starting Initial Nodes (Nodes that need no Args)")
        await asyncio.gather(*[nodeIDRunMap[node.id].on_event(PassInEvent(handle="args", value=[])) for node in initial_nodes])


        arg_receiving_nodes = self.parser.connectedNodes(self.argNode.id)
        await assign_handler.log(f"Workflow: This nodes will receive args: {[node.id for node in arg_receiving_nodes]}")
        await asyncio.gather(*[nodeIDRunMap[node.id].on_event(PassInEvent(handle="args",value=args)) for node in arg_receiving_nodes])

        while True:
            event: Union[PassOutEvent, DoneOutEvent] = await action_queue.get()
            await assign_handler.log(f"Workflow: Searching for nodes {event.node_id} on {event.handle}",level=ProgressLevel.DEBUG)
            # Action follows NODE_ID, OUTPUT_HANDLE, VALUES
            handle_nodes = self.parser.connectedNodesWithHandle(event.node_id, event.handle)
            await assign_handler.log(f"Workflow: Found the Following handles {handle_nodes}")

            for handle, node in handle_nodes:

                if isinstance(event, PassOutEvent):
                    if isinstance(node, diagram.ReturnNode):
                        await assign_handler.log("Workflow: Done")
                        return event.value
                    else:
                        await nodeIDRunMap[node.id].on_event(PassInEvent(handle=handle, value=event.value))


            action_queue.task_done()

        

    async def on_unreserve(self, unreserve_handler: UnreserveHandler, reserve_handler: ReserveHandler):
        await unreserve_handler.log("Workflow: Gently deleting our reservations")
        await asyncio.gather(*[res.end() for item, res in reserve_handler.context.items()])
        await unreserve_handler.log("Workflow: Unreserved")

    
    async def on_unprovide(self, handler_or_none):
        console.log("Unproviding")

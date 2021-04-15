from flow import diagram


class Parser:

    def __init__(self, di: diagram.Diagram) -> None:
        self.nodes  = [ node for node in di.elements if isinstance(node, diagram.Node)]
        self.edges = [ edge for edge in di.elements if isinstance(edge, diagram.Edge)]

        self.nodeIDNodeMap = {node.id: node for node in self.nodes}
        self.edgeIDEdgeMap = {edge.id: edge for edge in self.edges}

        self.argNode = next((node for node in  self.nodes if isinstance(node, diagram.ArgNode)), None) # We only want the first one
        self.kwargNode = next((node for node in  self.nodes if isinstance(node, diagram.KwargNode)), None) # We only want the first one
        self.returnNode = next((node for node in  self.nodes if isinstance(node, diagram.ReturnNode)), None) # We only want the first one

        self.non_generic_nodes = [node for node in self.nodes if not isinstance(node, (diagram.ArgNode, diagram.KwargNode, diagram.ReturnNode))]
    

    def connectedEdges(self, node_id: str, sourceHandle: str = None):
        return [edge for edge in self.edges if edge.source == node_id and (sourceHandle is None or edge.sourceHandle == sourceHandle)]

    def connectedNodes(self, node_id: str, sourceHandle: str = None, targetHandle: str = None):
        edg_ids = [edge.target for edge in self.connectedEdges(node_id, sourceHandle) if targetHandle is None or edge.targetHandle == targetHandle]
        nodes =  [node for node in self.nodes if node.id in edg_ids]
        return nodes


    def connectedNodesWithHandle(self, node_id: str, sourceHandle: str = None):
        edges = [edge for edge in self.connectedEdges(node_id, sourceHandle)]
        return [(edge.targetHandle, self.nodeIDNodeMap[edge.target]) for edge in edges]

    def getInitialNodes(self):
        non_kwargs_edge_targets = [edge.target for edge in self.edges if edge.source != self.kwargNode.id]
        non_generic_nodes_that_are_not_targets = [node for node in self.non_generic_nodes if node.id not in non_kwargs_edge_targets]
        return non_generic_nodes_that_are_not_targets

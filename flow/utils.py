from flow.models import Graph
from flow import diagram
from asgiref.sync import sync_to_async

@sync_to_async
def get_diagram_for_arkitekt_template_id(template_id) -> diagram.Diagram:
    graph = Graph.objects.get(template__arkitekt_id=template_id)
    return diagram.Diagram(**graph.diagram)





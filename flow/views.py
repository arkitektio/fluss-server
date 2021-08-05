
from flow.serializers import GraphSerializer
from flow.models import Graph
from rest_framework import viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


class GraphViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving users.
    """

    def retrieve(self, request, pk=None):
        queryset = Graph.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = GraphSerializer(user)
        return Response(serializer.data)
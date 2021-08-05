from rest_framework.serializers import ModelSerializer
from flow import models


class GraphSerializer(ModelSerializer):

    class Meta:
        model = models.Graph
        fields = ["diagram"]
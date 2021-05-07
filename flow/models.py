from django.db import models
from django.contrib.auth import get_user_model
import namegenerator
# Create your models here.


class FlowNode(models.Model):
    """ Mimics an Artikekt Node """
    arkitekt_id = models.CharField(max_length=1000, help_text="The identifier on the Arkitekt platform", unique=True)
    name = models.CharField(max_length=100, help_text="The name of this Flow")

    class Meta:
        arkitekt = True



class FlowTemplate(models.Model):
    """ Mimics an Artikekt template """
    arkitekt_id = models.CharField(max_length=4000,  help_text="The Template this one belongs two (Arkitekt identifier)", unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)


class FlowPod(models.Model):
    """ Mimics the Pod model of Arkitekt"""
    arkitekt_pod = models.CharField(max_length=1000, help_text="The Corresponding Pod in Arnheim", unique=True)



class Graph(models.Model):
    """ Graph is a Template for a Template"""
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE, null=True, help_text="Associated Node for this")
    template = models.ForeignKey(FlowTemplate, on_delete=models.CASCADE, null=True, help_text="Associated template for this")
    pod = models.ForeignKey(FlowPod, on_delete=models.CASCADE, null=True, help_text="Associated Node for this")
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    version = models.CharField(max_length=100, default="1.0alpha")
    name = models.CharField(max_length=100, null=True, default=namegenerator.gen)
    diagram = models.JSONField(null=True, blank=True)
    description = models.CharField(max_length=50000, default="Add a Description", blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        arkitekt = True

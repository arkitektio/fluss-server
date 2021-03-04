from django.db import models
from django.contrib.auth import get_user_model
import namegenerator
# Create your models here.



class Graph(models.Model):
    """ Graph is a Template for a Template"""
    node = models.CharField(max_length=1000, help_text="The Node this one belongs two", null=True, blank=True)
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    version = models.CharField(max_length=100, default="1.0alpha")
    name = models.CharField(max_length=100, null=True, default=namegenerator.gen)
    diagram = models.JSONField(null=True, blank=True)
    description = models.CharField(max_length=50000, default="Add a Description", blank=True, null=True)

    def __str__(self):
        return f"{self.name}"



class Template(models.Model):
    """ Mimics an Artikekt template """
    arkitekt_id = models.CharField(max_length=4000,  help_text="The Template this one belongs two (Arkitekt identifier)")
    port_id = models.CharField(max_length=100,help_text="The PortTemplate this one belongs two (Arkitekt identifier)" )


class Flow(models.Model):
    """ Mimics the Pod model of Arkitekt"""
    arkitekt_pod = models.CharField(max_length=1000, help_text="The Corresponding Pod in Arnheim")
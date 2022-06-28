from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Graph)
admin.site.register(Flow)
admin.site.register(Run)
admin.site.register(RunLog)

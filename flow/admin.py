from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Diagram)
admin.site.register(Flow)
admin.site.register(Run)
admin.site.register(RunLog)
admin.site.register(RunEvent)
admin.site.register(ReactiveTemplate)

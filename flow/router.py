from flow.views import GraphViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'graphs', GraphViewSet, basename='flows')

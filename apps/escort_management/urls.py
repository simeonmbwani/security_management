from rest_framework.routers import DefaultRouter
from .views import EscortMissionViewSet

router = DefaultRouter()
router.register("missions", EscortMissionViewSet, basename="escortmission")

urlpatterns = router.urls

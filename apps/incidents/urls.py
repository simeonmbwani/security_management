from rest_framework.routers import DefaultRouter
from .views import IncidentReportViewSet, IncidentMediaViewSet

router = DefaultRouter()
router.register("reports", IncidentReportViewSet, basename="incidentreport")
router.register("media", IncidentMediaViewSet, basename="incidentmedia")

urlpatterns = router.urls

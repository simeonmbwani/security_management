from rest_framework.routers import DefaultRouter
from .views import GuardPairViewSet, DutyRosterCycleViewSet, ShiftViewSet, ShiftHandoverViewSet, AttendanceViewSet

router = DefaultRouter()
router.register("pairs", GuardPairViewSet, basename="guardpair")
router.register("cycles", DutyRosterCycleViewSet, basename="rostercycle")
router.register("shifts", ShiftViewSet, basename="shift")
router.register("handovers", ShiftHandoverViewSet, basename="handover")
router.register("attendance", AttendanceViewSet, basename="attendance")

urlpatterns = router.urls

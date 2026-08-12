from rest_framework.routers import DefaultRouter
from .views import (
    LeaveBalanceViewSet, LeaveAccrualLogViewSet, PublicHolidayViewSet,
    PublicHolidayWorkLogViewSet, LeaveApplicationViewSet,
)

router = DefaultRouter()
router.register("balances", LeaveBalanceViewSet, basename="leavebalance")
router.register("accrual-logs", LeaveAccrualLogViewSet, basename="accrualog")
router.register("holidays", PublicHolidayViewSet, basename="publicholiday")
router.register("holiday-work-logs", PublicHolidayWorkLogViewSet, basename="holidayworklog")
router.register("applications", LeaveApplicationViewSet, basename="leaveapplication")

urlpatterns = router.urls

from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, StationViewSet, GuardProfileViewSet, EmployeeNumberTokenObtainPairView

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("stations", StationViewSet, basename="station")
router.register("guards", GuardProfileViewSet, basename="guard")
router.register("profiles", GuardProfileViewSet, basename="guardprofile")

urlpatterns = router.urls + [
    path("auth/login/", EmployeeNumberTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/register/", UserViewSet.as_view({"post": "register"}), name="user-register"),
]
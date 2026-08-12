from rest_framework.routers import DefaultRouter
from .views import KeyRegisterViewSet, EquipmentRegisterViewSet

router = DefaultRouter()
router.register("keys", KeyRegisterViewSet, basename="keyregister")
router.register("equipment", EquipmentRegisterViewSet, basename="equipmentregister")

urlpatterns = router.urls

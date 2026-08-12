from rest_framework.routers import DefaultRouter
from .views import CheckpointViewSet, PatrolViewSet, PatrolCheckpointLogViewSet

router = DefaultRouter()
router.register("checkpoints", CheckpointViewSet, basename="checkpoint")
router.register("patrols", PatrolViewSet, basename="patrol")
router.register("logs", PatrolCheckpointLogViewSet, basename="patrollog")

urlpatterns = router.urls

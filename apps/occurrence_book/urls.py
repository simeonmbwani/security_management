from rest_framework.routers import DefaultRouter
from .views import OccurrenceBookEntryViewSet, OccurrenceBookPhotoViewSet

router = DefaultRouter()
router.register("entries", OccurrenceBookEntryViewSet, basename="obentry")
router.register("photos", OccurrenceBookPhotoViewSet, basename="obphoto")

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter
from .views import ExamViewSet, ExamAssignmentViewSet

router = DefaultRouter()
router.register("exams", ExamViewSet, basename="exam")
router.register("assignments", ExamAssignmentViewSet, basename="examassignment")

urlpatterns = router.urls

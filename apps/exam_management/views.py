from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.permissions import IsSupervisorOrAdmin, ReadOnlyOrSupervisor
from .models import Exam, ExamAssignment
from .serializers import ExamSerializer, ExamAssignmentSerializer
from . import services


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.prefetch_related("assignments__guard").all()
    serializer_class = ExamSerializer
    permission_classes = [ReadOnlyOrSupervisor]
    filterset_fields = ["station"]

    @action(detail=True, methods=["post"], permission_classes=[IsSupervisorOrAdmin])
    def assign_guard(self, request, pk=None):
        exam = self.get_object()
        guard_id = request.data.get("guard")
        from apps.accounts.models import User
        guard = User.objects.get(id=guard_id)
        try:
            assignment = services.assign_exam_supervisor(exam, guard, request.user)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ExamAssignmentSerializer(assignment).data, status=201)

    @action(detail=True, methods=["post"], permission_classes=[IsSupervisorOrAdmin])
    def unassign_guard(self, request, pk=None):
        exam = self.get_object()
        guard_id = request.data.get("guard")
        from apps.accounts.models import User
        guard = User.objects.get(id=guard_id)
        services.unassign_exam_supervisor(exam, guard)
        return Response(status=204)


class ExamAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExamAssignment.objects.select_related("exam", "guard").all()
    serializer_class = ExamAssignmentSerializer
    permission_classes = [ReadOnlyOrSupervisor]
    filterset_fields = ["exam", "guard"]

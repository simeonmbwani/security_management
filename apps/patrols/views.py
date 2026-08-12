from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.permissions import IsOwnerOrSupervisor, ReadOnlyOrSupervisor
from .models import Checkpoint, Patrol, PatrolCheckpointLog
from .serializers import CheckpointSerializer, PatrolSerializer, PatrolCheckpointLogSerializer


class CheckpointViewSet(viewsets.ModelViewSet):
    queryset = Checkpoint.objects.select_related("station").filter(is_active=True)
    serializer_class = CheckpointSerializer
    permission_classes = [ReadOnlyOrSupervisor]
    filterset_fields = ["station", "is_active"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(user, 'role', '').lower()
        if role == "guard" and hasattr(user, 'guard_profile') and user.guard_profile.station:
            return qs.filter(station=user.guard_profile.station)
        return qs


class PatrolViewSet(viewsets.ModelViewSet):
    queryset = Patrol.objects.select_related("guard", "station").prefetch_related("logs").all()
    serializer_class = PatrolSerializer
    permission_classes = [IsOwnerOrSupervisor]
    filterset_fields = ["station", "guard", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = getattr(self.request.user, 'role', '').lower()
        if role == "guard":
            return qs.filter(guard=self.request.user)
        return qs

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        patrol = self.get_object()
        patrol.finished_at = timezone.now()
        patrol.status = Patrol.Status.COMPLETED
        patrol.save(update_fields=["finished_at", "status"])
        return Response(PatrolSerializer(patrol).data)

    @action(detail=True, methods=["post"])
    def log_checkpoint(self, request, pk=None):
        """Record a checkpoint visit within this patrol."""
        patrol = self.get_object()
        data = request.data.copy()
        data["patrol"] = str(patrol.id)
        serializer = PatrolCheckpointLogSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)


class PatrolCheckpointLogViewSet(viewsets.ModelViewSet):
    queryset = PatrolCheckpointLog.objects.select_related("patrol", "checkpoint").all()
    serializer_class = PatrolCheckpointLogSerializer
    permission_classes = [IsOwnerOrSupervisor]
    filterset_fields = ["patrol", "checkpoint", "is_flagged"]

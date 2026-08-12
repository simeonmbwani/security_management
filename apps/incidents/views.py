from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.permissions import IsOwnerOrSupervisor, IsSupervisorOrAdmin
from .models import IncidentReport, IncidentMedia
from .serializers import IncidentReportSerializer, IncidentMediaSerializer


class IncidentReportViewSet(viewsets.ModelViewSet):
    """
    Guards create incident reports (the "emergency button"). Creation should
    also trigger a push/SMS notification to supervisors — see
    notifications.services.notify_incident, wired via a signal.
    """
    queryset = IncidentReport.objects.select_related("reported_by", "station").prefetch_related("media").all()
    serializer_class = IncidentReportSerializer
    permission_classes = [IsOwnerOrSupervisor]
    filterset_fields = ["station", "incident_type", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(user, 'role', '').lower()
        if role == "guard":
            return qs.filter(reported_by=user)
        return qs

    @action(detail=True, methods=["post"], permission_classes=[IsSupervisorOrAdmin])
    def acknowledge(self, request, pk=None):
        incident = self.get_object()
        incident.status = IncidentReport.Status.ACKNOWLEDGED
        incident.acknowledged_by = request.user
        incident.save(update_fields=["status", "acknowledged_by"])
        return Response(IncidentReportSerializer(incident).data)

    @action(detail=True, methods=["post"], permission_classes=[IsSupervisorOrAdmin])
    def resolve(self, request, pk=None):
        incident = self.get_object()
        incident.status = IncidentReport.Status.RESOLVED
        incident.resolved_at = timezone.now()
        incident.save(update_fields=["status", "resolved_at"])
        return Response(IncidentReportSerializer(incident).data)


class IncidentMediaViewSet(viewsets.ModelViewSet):
    queryset = IncidentMedia.objects.all()
    serializer_class = IncidentMediaSerializer
    permission_classes = [IsOwnerOrSupervisor]
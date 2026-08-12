from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.permissions import IsSupervisorOrAdmin, ReadOnlyOrSupervisor
from .models import EscortMission
from .serializers import EscortMissionSerializer


class EscortMissionViewSet(viewsets.ModelViewSet):
    queryset = EscortMission.objects.select_related("escort_guard").all()
    serializer_class = EscortMissionSerializer
    permission_classes = [ReadOnlyOrSupervisor]
    filterset_fields = ["escort_guard"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == "guard":
            return qs.filter(escort_guard=self.request.user)
        return qs

    @action(detail=False, methods=["get"])
    def mine(self, request):
        return Response(EscortMissionSerializer(self.get_queryset(), many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[IsSupervisorOrAdmin])
    def complete(self, request, pk=None):
        """Mark the escort mission as returned, freeing the guard for normal roster."""
        mission = self.get_object()
        mission.return_date = timezone.now()
        mission.mileage_in = request.data.get("mileage_in", mission.mileage_in)
        mission.remarks = request.data.get("remarks", mission.remarks)
        mission.save()
        return Response(EscortMissionSerializer(mission).data)

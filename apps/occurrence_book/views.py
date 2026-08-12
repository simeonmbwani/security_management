from rest_framework import viewsets, permissions
from core.permissions import IsOwnerOrSupervisor
from .models import OccurrenceBookEntry, OccurrenceBookPhoto
from .serializers import OccurrenceBookEntrySerializer, OccurrenceBookPhotoSerializer


class OccurrenceBookEntryViewSet(viewsets.ModelViewSet):
    """
    Guards create their own OB entries and can view history/search past
    entries. Supervisors can add comments and see everything at their
    station.
    """
    queryset = OccurrenceBookEntry.objects.select_related("guard", "station", "supervisor").prefetch_related("photos").all()
    serializer_class = OccurrenceBookEntrySerializer
    permission_classes = [IsOwnerOrSupervisor]
    filterset_fields = ["station", "guard", "shift", "supervisor"]
    search_fields = ["entry_number", "occurrence", "check_record", "location"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "guard":
            # Guards see their own entries plus the shared station log (read access).
            return qs
        return qs


class OccurrenceBookPhotoViewSet(viewsets.ModelViewSet):
    queryset = OccurrenceBookPhoto.objects.all()
    serializer_class = OccurrenceBookPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]

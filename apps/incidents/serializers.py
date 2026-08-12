from django.utils import timezone
from rest_framework import serializers
from .models import IncidentReport, IncidentMedia


class IncidentMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentMedia
        fields = ["id", "incident", "media_type", "file", "uploaded_at"]


class IncidentReportSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.CharField(source="reported_by.get_full_name", read_only=True)
    media = IncidentMediaSerializer(many=True, read_only=True)

    class Meta:
        model = IncidentReport
        fields = [
            "id", "station", "reported_by", "reported_by_name", "incident_type", "description",
            "latitude", "longitude", "status", "acknowledged_by", "resolved_at", "created_at", "media",
        ]
        read_only_fields = ["station", "reported_by", "status", "acknowledged_by", "resolved_at", "created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        station = getattr(getattr(user, "guard_profile", None), "station", None)
        
        if station is None:
            from apps.shifts.models import Shift
            shift = Shift.objects.filter(guard=user, date=timezone.localdate()).select_related("station").first()
            station = shift.station if shift else None
            
        if station is None:
            raise serializers.ValidationError({
                "station": "No station is assigned to this guard. Ask an administrator to assign a station before reporting an emergency."
            })
            
        validated_data["reported_by"] = user
        validated_data["station"] = station
        
        # Create the incident report entry
        incident = super().create(validated_data)
        
        # Automatically process and attach any files sent via multipart/form-data requests
        request = self.context.get("request")
        if request and request.FILES:
            for _, files_list in request.FILES.lists():
                for f in files_list:
                    media_type = IncidentMedia.MediaType.PHOTO
                    if f.content_type and 'video' in f.content_type:
                        media_type = IncidentMedia.MediaType.VIDEO
                    elif f.content_type and 'audio' in f.content_type:
                        media_type = IncidentMedia.MediaType.AUDIO
                        
                    IncidentMedia.objects.create(
                        incident=incident,
                        media_type=media_type,
                        file=f
                    )
                    
        return incident
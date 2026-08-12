from rest_framework import serializers
from .models import OccurrenceBookEntry, OccurrenceBookPhoto


class OccurrenceBookPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OccurrenceBookPhoto
        fields = ["id", "entry", "image", "uploaded_at"]


class OccurrenceBookEntrySerializer(serializers.ModelSerializer):
    guard_name = serializers.CharField(source="guard.get_full_name", read_only=True)
    photos = OccurrenceBookPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = OccurrenceBookEntry
        fields = [
            "id", "entry_number", "station", "guard", "guard_name", "shift", "occurrence",
            "check_record", "location", "signature", "supervisor", "supervisor_comment",
            "photos", "created_at",
        ]
        read_only_fields = ["entry_number", "station", "guard", "created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        # A guard must never have to (or be able to) choose another station
        # when writing an OB entry from the mobile app.
        station = getattr(getattr(user, "guard_profile", None), "station", None)
        if station is None:
            raise serializers.ValidationError({"station": "Assign this guard to a station before saving an OB entry."})
        validated_data["guard"] = user
        validated_data["station"] = station
        return super().create(validated_data)

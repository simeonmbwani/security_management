from rest_framework import serializers
from .models import Visitor


class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = ["id", "station", "full_name", "national_id", "phone", "purpose",
                  "vehicle_registration", "host", "photo", "time_in", "time_out", "recorded_by"]
        read_only_fields = ["time_in", "recorded_by"]

    def create(self, validated_data):
        validated_data["recorded_by"] = self.context["request"].user
        return super().create(validated_data)

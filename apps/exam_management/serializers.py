from rest_framework import serializers
from .models import Exam, ExamAssignment


class ExamSerializer(serializers.ModelSerializer):
    assigned_guards = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = ["id", "station", "name", "venue", "start_date", "end_date",
                  "created_by", "created_at", "assigned_guards"]
        read_only_fields = ["created_by", "created_at"]

    def get_assigned_guards(self, obj):
        return [str(a.guard) for a in obj.assignments.select_related("guard")]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class ExamAssignmentSerializer(serializers.ModelSerializer):
    guard_name = serializers.CharField(source="guard.get_full_name", read_only=True)
    exam_name = serializers.CharField(source="exam.name", read_only=True)

    class Meta:
        model = ExamAssignment
        fields = ["id", "exam", "exam_name", "guard", "guard_name", "assigned_by", "created_at"]
        read_only_fields = ["assigned_by", "created_at"]

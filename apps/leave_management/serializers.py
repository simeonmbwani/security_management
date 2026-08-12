from rest_framework import serializers
from .models import LeaveBalance, LeaveAccrualLog, PublicHoliday, PublicHolidayWorkLog, LeaveApplication


class LeaveBalanceSerializer(serializers.ModelSerializer):
    guard_name = serializers.CharField(source="guard.get_full_name", read_only=True)
    leave_type_display = serializers.CharField(source="get_leave_type_display", read_only=True)

    class Meta:
        model = LeaveBalance
        fields = [
            "id", "guard", "guard_name", "leave_type", "leave_type_display",
            "available_days", "used_days", "expired_days", "last_accrued_month"
        ]
        read_only_fields = ["guard", "available_days", "used_days", "expired_days", "last_accrued_month"]


class LeaveAccrualLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveAccrualLog
        fields = ["id", "balance", "amount", "reason", "created_at"]
        read_only_fields = ["created_at"]


class PublicHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHoliday
        fields = ["id", "name", "date"]


class PublicHolidayWorkLogSerializer(serializers.ModelSerializer):
    guard_name = serializers.CharField(source="guard.get_full_name", read_only=True)
    holiday_name = serializers.CharField(source="holiday.name", read_only=True)

    class Meta:
        model = PublicHolidayWorkLog
        fields = ["id", "guard", "guard_name", "holiday", "holiday_name", "days_credited", "created_at"]
        read_only_fields = ["created_at"]


class LeaveApplicationSerializer(serializers.ModelSerializer):
    guard_name = serializers.CharField(source="guard.get_full_name", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.get_full_name", read_only=True)
    days_requested = serializers.IntegerField(read_only=True)
    leave_type_display = serializers.CharField(source="get_leave_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = LeaveApplication
        fields = [
            "id", "guard", "guard_name", "leave_type", "leave_type_display",
            "start_date", "end_date", "days_requested", "reason", "status",
            "status_display", "reviewed_by", "reviewed_by_name", "review_comment",
            "created_at", "updated_at"
        ]
        read_only_fields = ["guard", "status", "reviewed_by", "review_comment", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["guard"] = self.context["request"].user
        return super().create(validated_data)
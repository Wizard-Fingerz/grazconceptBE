from rest_framework import serializers

from definition.models import TableDropDownDefinition
from definition.serializers import TableDropDownDefinitionSerializer
from .models import SupportTicket, SupportTicketMessage


class SupportTicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicketMessage
        fields = ["id", "sender", "text", "timestamp"]

class SupportTicketSerializer(serializers.ModelSerializer):
    messages = SupportTicketMessageSerializer(many=True, read_only=True)
    status = TableDropDownDefinitionSerializer(read_only=True)
    status_id = serializers.PrimaryKeyRelatedField(
        queryset=TableDropDownDefinition.objects.filter(table_name="support_ticket_status"),
        source="status",
        write_only=True
    )
    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "user",
            "subject",
            "status",
            "status_id",
            "created_at",
            "last_reply",
            "messages"
        ]
        read_only_fields = ["id", "created_at", "last_reply", "user", "messages", "status"]
        extra_kwargs = {
            "subject": {"required": True},
        }

    def create(self, validated_data):
        # user should be set from context (request.user)
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        return super().create(validated_data)

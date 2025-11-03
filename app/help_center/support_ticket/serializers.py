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
    # status is only read-only, no status_id field for writing
    # (user cannot set status at creation or update via serializer)

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "user",
            "subject",
            "status",
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

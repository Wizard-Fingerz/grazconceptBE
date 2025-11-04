from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'title',
            'message',
            'notification_type',
            'data',
            'is_read',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']


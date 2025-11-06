from rest_framework import serializers
from .models import ChatSession, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'email')

class MessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    recipient = UserMiniSerializer(read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'chat_session',
            'sender',
            'recipient',
            'sender_type',
            'message',
            'attachment',
            'attachment_url',
            'timestamp',
            'read',
        ]
        read_only_fields = ['id', 'timestamp', 'read']

    def get_attachment_url(self, obj):
        if obj.attachment and hasattr(obj.attachment, 'url'):
            request = self.context.get('request')
            url = obj.attachment.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None

class ChatSessionSerializer(serializers.ModelSerializer):
    customer = UserMiniSerializer(read_only=True)
    agent = UserMiniSerializer(read_only=True)
    last_message_at = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            'id',
            'customer',
            'agent',
            'status',
            'priority',
            'service_title',
            'created_at',
            'updated_at',
            'last_message_at',
            'unread_count',
            'messages',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'last_message_at', 'unread_count', 'messages'
        ]

    def get_last_message_at(self, obj):
        return obj.last_message_at()

    def get_unread_count(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            return obj.unread_count_for_user(user)
        return 0

    def get_messages(self, obj):
        # Optionally provide only the last N messages (could accept limit param in context)
        limit = self.context.get('messages_limit', 30)
        msgs = obj.messages.order_by('-timestamp')[:limit]
        return MessageSerializer(msgs, many=True, context=self.context).data


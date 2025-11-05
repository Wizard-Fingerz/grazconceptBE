from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import ChatSession, Message

class ChatSessionResource(resources.ModelResource):
    class Meta:
        model = ChatSession
        fields = (
            'id',
            'customer',
            'customer',
            'agent',
            'agent',
            'status',
            'priority',
            'service_title',
            'created_at',
            'updated_at',
        )


@admin.register(ChatSession)
class ChatSessionAdmin(ImportExportModelAdmin):
    resource_class = ChatSessionResource
    list_display = ['id', 'customer', 'agent', 'status', 'priority', 'created_at', 'updated_at']
    search_fields = ['customer', 'customer', 'customer', 'agent', 'agent', 'agent', 'service_title']
    list_filter = ['status', 'priority', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


class MessageResource(resources.ModelResource):
    class Meta:
        model = Message
        fields = (
            'id',
            'chat_session',
            'sender',
            'recipient',
            'sender_type',
            'message',
            'timestamp',
            'read',
        )

@admin.register(Message)
class MessageAdmin(ImportExportModelAdmin):
    resource_class = MessageResource
    list_display = ['id', 'chat_session', 'sender', 'recipient', 'sender_type', 'message', 'read', 'timestamp']
    search_fields = ['sender', 'recipient', 'message']
    list_filter = ['sender_type', 'read', 'timestamp', 'chat_session']
    readonly_fields = ['timestamp']


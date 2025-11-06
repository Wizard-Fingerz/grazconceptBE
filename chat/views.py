from rest_framework import viewsets, permissions
from .models import ChatSession, Message
from .serializers import ChatSessionSerializer, MessageSerializer
from django.db import models

class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for listing, retrieving, creating, and updating chat sessions.
    """
    queryset = ChatSession.objects.all().order_by('-created_at')
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatSession.objects.filter(
            models.Q(customer=user) | models.Q(agent=user)
        ).order_by('-created_at')


class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for listing, retrieving, creating, and updating chat messages.
    """
    queryset = Message.objects.all().order_by('timestamp')
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        chat_id = self.request.query_params.get('chat_session')
        queryset = Message.objects.filter(
            models.Q(sender=user) | models.Q(recipient=user)
        )
        if chat_id is not None:
            queryset = queryset.filter(chat_session_id=chat_id)
        return queryset.order_by('timestamp')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

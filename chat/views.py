from rest_framework import viewsets, permissions
from .models import ChatSession, Message
from .serializers import ChatSessionSerializer, MessageSerializer
from django.db import models

# Custom action for uploading attachments
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404


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

    @action(detail=False, methods=['post'], url_path='upload_attachment')
    def upload_attachment(self, request):
        """
        Endpoint for uploading an attachment to a chat by chat_id and user_id.

        Request POST body/form-data should include:
            - file (the attachment)
            - chat_id
            - user_id (recipient)
        """
        file = request.FILES.get('file')
        chat_id = request.data.get('chat_id')
        recipient_id = request.data.get('user_id')
        sender = request.user

        if not all([file, chat_id, recipient_id]):
            return Response(
                {"detail": "Missing file, chat_id, or user_id."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate chat session & recipient
        chat_session = get_object_or_404(ChatSession, id=chat_id)
        recipient = get_object_or_404(
            chat_session.customer.__class__, id=recipient_id)
        # Determine sender_type
        sender_type = "customer" if chat_session.customer_id == sender.id else "agent"

        # Create message with attachment only (no message text required)
        message = Message.objects.create(
            chat_session=chat_session,
            sender=sender,
            recipient=recipient,
            sender_type=sender_type,
            attachment=file,
            message="",  # No text required for attachment upload
        )
        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

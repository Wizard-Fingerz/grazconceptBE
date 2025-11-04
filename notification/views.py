from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets, permissions
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows notifications to be viewed or edited.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return notifications belonging to the current authenticated user
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # Automatically assign the notification to the current user
        serializer.save(user=self.request.user)


@api_view(['GET'])
def websocket_info(request):
    """
    WebSocket connection details.
    ---
    description: |
        Connect via WebSocket to receive real-time notifications.

        **WebSocket URL:** `wss://yourdomain.com/ws/notifications/`

        Once connected, messages will arrive in this format:
        ```json
        {
          "type": "notification",
          "message": "New comment added."
        }
        ```

        You can also send pings or control messages via the WebSocket.
    """
    return Response({
        "websocket_url": "wss://yourdomain.com/ws/notifications/"
    })


@api_view(['GET'])
def websocket_doc(request):
    return Response({"message": "WebSocket endpoint documentation only."})

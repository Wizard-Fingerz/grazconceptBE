from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets, permissions

from app.views import CustomPagination
from .models import Notification
from .serializers import NotificationSerializer


from rest_framework.decorators import action
from rest_framework import status


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows notifications to be viewed or edited.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        # Only return notifications belonging to the current authenticated user
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # Automatically assign the notification to the current user
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """
        Mark all notifications of the current user as read.
        """
        updated_count = Notification.objects.filter(
            user=request.user, is_read=False).update(is_read=True)
        return Response(
            {"status": "success", "marked_as_read": updated_count},
            status=status.HTTP_200_OK
        )


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

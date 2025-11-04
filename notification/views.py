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

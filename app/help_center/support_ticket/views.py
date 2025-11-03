from rest_framework import viewsets, permissions
from .models import SupportTicket
from .serializers import SupportTicketSerializer

class SupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all().select_related("user", "status").prefetch_related("messages")
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return tickets created by the current user
        user = self.request.user
        return self.queryset.filter(user=user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


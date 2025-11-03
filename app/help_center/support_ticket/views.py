from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from .models import SupportTicket
from .serializers import SupportTicketSerializer
from .serializers import SupportTicketMessageSerializer
from rest_framework.exceptions import NotFound, PermissionDenied

class SupportTicketViewSet(viewsets.ModelViewSet):
    """
    Endpoints:
    - GET    /api/support/tickets/                      : List support tickets of current user
    - POST   /api/support/tickets/                      : Create a new ticket (expects 'subject', 'message')
    - GET    /api/support/tickets/<id>/                 : Get details of a ticket (current user)
    - POST   /api/support/tickets/<id>/reply/           : Add reply to a ticket (expects 'message')
    """
    queryset = SupportTicket.objects.all().select_related("user", "status").prefetch_related("messages")
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return tickets created by the current user (or support agents, if needed)
        user = self.request.user
        return self.queryset.filter(user=user).order_by("-created_at")

    def perform_create(self, serializer):
        # API expects { "subject": ..., "message": ... }
        initial_data = self.request.data
        message_text = initial_data.get("message")
        ticket = serializer.save(user=self.request.user)
        # Optionally, create the first SupportTicketMessage attached to the ticket
        from .models import SupportTicketMessage
        SupportTicketMessage.objects.create(
            ticket=ticket,
            sender="user",
            text=message_text
        )

    @action(detail=True, methods=["post"], url_path="reply")
    def reply(self, request, pk=None):
        """
        POST /api/support/tickets/<id>/reply/
        Body: { "message": "..."}
        """
        try:
            ticket = self.get_queryset().get(pk=pk)
        except SupportTicket.DoesNotExist:
            raise NotFound("Ticket not found.")
        if ticket.status and getattr(ticket.status, "name", None) == "Closed":
            return Response({"error": "Ticket is closed."}, status=status.HTTP_400_BAD_REQUEST)
        # Anyone but original user is denied
        if ticket.user != request.user:
            raise PermissionDenied("You do not have permission to reply to this ticket.")

        message = request.data.get("message", "").strip()
        if not message:
            return Response({"error": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Add the message as a user reply
        from .models import SupportTicketMessage
        msg_obj = SupportTicketMessage.objects.create(
            ticket=ticket,
            sender="user",
            text=message
        )
        serializer = SupportTicketMessageSerializer(msg_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

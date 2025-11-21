from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from .models import SavingsPlan
from .serializers import SavingsPlanSerializer

class SavingsPlanViewSet(viewsets.ModelViewSet):
    serializer_class = SavingsPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only show savings plans belonging to the authenticated user
        return SavingsPlan.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Set the user field automatically so users cannot create for others
        data = request.data.copy()
        data["user"] = request.user.pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        # Cancel a savings plan if it's active and belongs to the user
        try:
            plan = self.get_queryset().get(pk=pk)
        except SavingsPlan.DoesNotExist:
            return Response({"detail": "Savings plan not found."}, status=status.HTTP_404_NOT_FOUND)
        if plan.status != "active":
            return Response({"detail": "Only active savings plans can be cancelled."}, status=status.HTTP_400_BAD_REQUEST)
        plan.status = "cancelled"
        plan.updated_at = timezone.now()
        plan.save(update_fields=["status", "updated_at"])
        return Response({"detail": "Savings plan cancelled successfully."}, status=status.HTTP_200_OK)

from rest_framework import viewsets, permissions
from .models import SavingsPlan
from .serializers import SavingsPlanSerializer

class SavingsPlanViewSet(viewsets.ModelViewSet):
    queryset = SavingsPlan.objects.all()
    serializer_class = SavingsPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only savings plans belonging to the authenticated user
        return SavingsPlan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign the savings plan to the logged-in user
        serializer.save(user=self.request.user)


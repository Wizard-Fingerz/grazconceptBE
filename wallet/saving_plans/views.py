from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import SavingsPlan
from .serializers import SavingsPlanSerializer

class SavingsPlanViewSet(viewsets.ModelViewSet):
    queryset = SavingsPlan.objects.all()
    serializer_class = SavingsPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only savings plans belonging to the authenticated user
        return SavingsPlan.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Copy data and set the user to the request user before passing to the serializer
        data = request.data.copy()
        data['user'] = request.user.pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


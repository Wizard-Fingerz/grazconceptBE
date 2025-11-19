from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status

from .models import CVProfile
from .serializers import CVProfileSerializer

class CVProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint to create, retrieve, update, or delete a CVProfile and all its details,
    including nested education, experience, certifications, skills, languages, publications.
    All details are handled with a single endpoint.
    """
    queryset = CVProfile.objects.all()
    serializer_class = CVProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users only see their own CV profiles unless staff/superuser.
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return CVProfile.objects.all()
        return CVProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        # Sets the user as owner of the profile on creation
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Allow POST to create full CV, including related objects via nested structures.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # Handles PUT/PATCH to update the profile with all its details
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


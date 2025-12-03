from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from app.views import CustomPagination
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
    pagination_class = CustomPagination

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
        # Make sure the request user is assigned as the profile owner before serializing
        data = request.data.copy()
        data['user'] = request.user.pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # Make sure the request user is assigned as the profile owner before serializing
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        data['user'] = request.user.pk
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

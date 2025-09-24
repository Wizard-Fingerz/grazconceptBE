from rest_framework import viewsets, permissions
from rest_framework.response import Response

from app.views import CustomPagination
from app.visa.study.serializers import StudyVisaApplicationSerializer
from .models import StudyVisaApplication
from rest_framework.permissions import IsAuthenticated


class StudyVisaApplicationViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing hotel booking instances.
    """
    queryset = StudyVisaApplication.objects.all().order_by('-application_date')
    serializer_class = StudyVisaApplicationSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['applicant'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

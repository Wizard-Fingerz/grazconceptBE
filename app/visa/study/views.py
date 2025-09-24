from rest_framework import viewsets, permissions

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

    def perform_create(self, serializer):
        # Map incoming camelCase keys to model fields if necessary
        data = self.request.data.copy()
       
        serializer.save(**data)


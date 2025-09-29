from rest_framework import viewsets
from rest_framework import permissions
from .models import WorkOrganization
from .serializers import WorkOrganizationSerializer
from app.views import CustomPagination



class WorkOrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows work organizations to be viewed or edited.
    """
    queryset = WorkOrganization.objects.all()
    serializer_class = WorkOrganizationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

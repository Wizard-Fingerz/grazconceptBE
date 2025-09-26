from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from app.views import CustomPagination
from .models import AdBanner
from .serializers import AdBannerSerializer

class AdBannerViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing AdBanner instances.
    """
    queryset = AdBanner.objects.all().order_by('-created_at')
    serializer_class = AdBannerSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination



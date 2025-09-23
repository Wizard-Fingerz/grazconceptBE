from rest_framework import viewsets, permissions

from app.views import CustomPagination
from .models import HotelBooking
from rest_framework.permissions import IsAuthenticated
from .serializers import HotelBookingSerializer

class HotelBookingViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing hotel booking instances.
    """
    queryset = HotelBooking.objects.all().order_by('-created_at')
    serializer_class = HotelBookingSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Map incoming camelCase keys to model fields if necessary
        data = self.request.data.copy()
       
        serializer.save(**data)


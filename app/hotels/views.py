from rest_framework import viewsets, permissions
from .models import HotelBooking
from rest_framework.permissions import IsAuthenticated
from .serializers import HotelBookingSerializer

class HotelBookingViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing hotel booking instances.
    """
    queryset = HotelBooking.objects.all().order_by('-created_at')
    serializer_class = HotelBookingSerializer

    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Map incoming camelCase keys to model fields if necessary
        data = self.request.data.copy()
        mapped_data = {
            'destination': data.get('destination'),
            'check_in': data.get('checkIn'),
            'check_out': data.get('checkOut'),
            'adults': data.get('adults'),
            'children': data.get('children'),
            'rooms': data.get('rooms'),
            'traveling_with_pets': data.get('travelingWithPets'),
        }
        serializer.save(**mapped_data)

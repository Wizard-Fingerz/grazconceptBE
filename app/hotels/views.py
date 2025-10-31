from rest_framework import viewsets, permissions

from app.views import CustomPagination
from .models import Hotel, HotelBooking
from rest_framework.permissions import IsAuthenticated
from .serializers import HotelBookingSerializer, HotelSerializer

class HotelBookingViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing hotel booking instances.
    Shows only the user's bookings if the user is a "Customer".
    """
    queryset = HotelBooking.objects.all().order_by('-created_at')
    serializer_class = HotelBookingSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        If the user's user_type.term is "Customer", restrict to their own bookings.
        Otherwise, show all bookings.
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Check if the user is a Customer based on user_type.term
        is_customer = hasattr(user, 'user_type') and getattr(user.user_type, 'term', '').lower() == 'customer'
        if is_customer:
            client = getattr(user, 'client', None)
            if client:
                queryset = queryset.filter(applicant=client)
            else:
                # Defensive: no client object; return none
                return queryset.none()
        return queryset

    def perform_create(self, serializer):
        # Map incoming camelCase keys to model fields if necessary
        data = self.request.data.copy()
       
        serializer.save(**data)


class HotelViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing hotel booking instances.
    """
    queryset = Hotel.objects.all().order_by('-created_at')
    serializer_class = HotelSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Map incoming camelCase keys to model fields if necessary
        data = self.request.data.copy()
       
        serializer.save(**data)


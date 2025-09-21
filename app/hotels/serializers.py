from rest_framework import serializers
from .models import HotelBooking

class HotelBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelBooking
        fields = [
            'id',
            'destination',
            'check_in',
            'check_out',
            'adults',
            'children',
            'rooms',
            'traveling_with_pets',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

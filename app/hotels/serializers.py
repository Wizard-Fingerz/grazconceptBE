from rest_framework import serializers
from .models import Hotel, HotelBooking

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

class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = [
            'id',
            'image',
            'name',
            'address',
            'city',
            'country',
            'latitude',
            'longitude',
            'rating',
            'reviews',
            'price',
            'description',
            'amenities',
            'phone_number',
            'email',
            'website',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

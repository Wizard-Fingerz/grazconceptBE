from rest_framework import serializers
from .models import VacationOffer, VacationOfferIncludedItem, VacationOfferImage
from django_countries.serializers import CountryFieldMixin

class VacationOfferIncludedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacationOfferIncludedItem
        fields = [
            'id',
            'name',
            'description',
        ]
        read_only_fields = ['id']

class VacationOfferImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacationOfferImage
        fields = [
            'id',
            'image',
            'caption',
        ]
        read_only_fields = ['id']

class VacationOfferSerializer(CountryFieldMixin, serializers.ModelSerializer):
    included_items = VacationOfferIncludedItemSerializer(many=True, read_only=True)
    images = VacationOfferImageSerializer(many=True, read_only=True)

    class Meta:
        model = VacationOffer
        fields = [
            'id',
            'title',
            'description',
            'destination',
            'start_date',
            'end_date',
            'price',
            'currency',
            'per_seat',
            'hotel_stars',
            'image',
            'is_active',
            'created_at',
            'updated_at',
            'included_items',
            'images',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

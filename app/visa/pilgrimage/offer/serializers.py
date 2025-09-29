from rest_framework import serializers
from .models import PilgrimageOffer, PilgrimageOfferIncludedItem, PilgrimageOfferImage

class PilgrimageOfferIncludedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PilgrimageOfferIncludedItem
        fields = ['id', 'name', 'description']

class PilgrimageOfferImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PilgrimageOfferImage
        fields = ['id', 'image', 'caption']

class PilgrimageOfferSerializer(serializers.ModelSerializer):
    included_items = PilgrimageOfferIncludedItemSerializer(many=True, read_only=True)
    images = PilgrimageOfferImageSerializer(many=True, read_only=True)

    class Meta:
        model = PilgrimageOffer
        fields = [
            'id',
            'title',
            'description',
            'pilgrimage_type',
            'destination',
            'city',
            'start_date',
            'end_date',
            'price',
            'currency',
            'sponsorship',
            'sponsor_name',
            'seats_available',
            'per_seat',
            'image',
            'is_active',
            'created_at',
            'updated_at',
            'included_items',
            'images',
        ]

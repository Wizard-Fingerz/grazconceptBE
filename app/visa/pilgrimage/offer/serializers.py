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
    pilgrimage_type_display = serializers.ReadOnlyField()
    sponsorship_display = serializers.ReadOnlyField()

    class Meta:
        model = PilgrimageOffer
        fields = [
            'id',
            'title',
            'description',
            'pilgrimage_type',
            'pilgrimage_type_display',
            'destination',
            'city',
            'start_date',
            'end_date',
            'price',
            'currency',
            'sponsorship',
            'sponsorship_display',
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
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'included_items',
            'images',
            'pilgrimage_type_display',
            'sponsorship_display',
        ]

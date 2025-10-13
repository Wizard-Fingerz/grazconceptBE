from rest_framework import serializers
from .models import (
    PilgrimageOffer,
    PilgrimageOfferIncludedItem,
    PilgrimageOfferImage,
    PilgrimageVisaApplication,
)

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
    pilgrimage_type_display = serializers.SerializerMethodField()
    sponsorship_display = serializers.SerializerMethodField()

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

    def get_pilgrimage_type_display(self, obj):
        return obj.pilgrimage_type_display

    def get_sponsorship_display(self, obj):
        return obj.sponsorship_display

class PilgrimageVisaApplicationSerializer(serializers.ModelSerializer):
    offer_title = serializers.CharField(source="offer.title", read_only=True)
    destination = serializers.CharField(source="offer.destination", read_only=True)
    applicant_name = serializers.SerializerMethodField()
    pilgrimage_type_display = serializers.SerializerMethodField()
    accommodation_type_display = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PilgrimageVisaApplication
        fields = [
            "id",
            "offer",
            "offer_title",
            "destination",
            "applicant",
            "applicant_name",
            "passport_number",
            "date_of_birth",
            "pilgrimage_type",
            "pilgrimage_type_display",
            "accommodation_type",
            "accommodation_type_display",
            "preferred_travel_date",
            "group_travel",
            "passport_photo",
            "medical_certificate",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "offer_title",
            "destination",
            "applicant_name",
            "pilgrimage_type_display",
            "accommodation_type_display"
        ]

    def get_applicant_name(self, obj):
        if hasattr(obj.applicant, "get_full_name"):
            name = obj.applicant.get_full_name()
            if name:
                return name
        if hasattr(obj.applicant, "user") and hasattr(obj.applicant.user, "username"):
            return obj.applicant.user.username
        if hasattr(obj.applicant, "username"):
            return obj.applicant.username
        return None

    def get_pilgrimage_type_display(self, obj):
        # Use the dropdown term if available
        if obj.pilgrimage_type:
            return obj.pilgrimage_type.term
        return None

    def get_accommodation_type_display(self, obj):
        if obj.accommodation_type:
            return obj.accommodation_type.term
        return None

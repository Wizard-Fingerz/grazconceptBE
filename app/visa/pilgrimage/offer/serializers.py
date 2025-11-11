from rest_framework import serializers
from .models import (
    PilgrimageOffer,
    PilgrimageOfferIncludedItem,
    PilgrimageOfferImage,
    PilgrimageVisaApplication,
    PilgrimageVisaApplicationComment,
)

# Included Item Serializer
class PilgrimageOfferIncludedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PilgrimageOfferIncludedItem
        fields = ['id', 'name', 'description']

# Image Serializer
class PilgrimageOfferImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PilgrimageOfferImage
        fields = ['id', 'image', 'caption']

# Pilgrimage Visa Application Comment Serializer
class PilgrimageVisaApplicationCommentSerializer(serializers.ModelSerializer):
    sender_type = serializers.CharField(read_only=True)
    sender_display = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PilgrimageVisaApplicationComment
        fields = [
            "id",
            "visa_application",
            "applicant",
            "admin",
            "text",
            "created_at",
            "is_read_by_applicant",
            "is_read_by_admin",
            "attachment",
            "sender_type",
            "sender_display",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "sender_type",
            "sender_display",
        ]

    def get_sender_display(self, obj):
        # Replicate logic from sender_display property in the model
        if obj.applicant:
            return {
                "type": "applicant",
                "name": getattr(obj.applicant, "get_full_name", lambda: None)() or getattr(getattr(obj.applicant, "user", None), "username", None),
                "id": obj.applicant.id,
            }
        elif obj.admin:
            if hasattr(obj.admin, "get_full_name"):
                name = obj.admin.get_full_name()
            else:
                name = getattr(obj.admin, "username", None)
            return {
                "type": "admin",
                "name": name,
                "id": obj.admin.id,
            }
        return {"type": "unknown"}

# Pilgrimage Offer Serializer
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

# Visa Application Serializer
class PilgrimageVisaApplicationSerializer(serializers.ModelSerializer):
    offer_title = serializers.CharField(source="offer.title", read_only=True)
    destination = serializers.CharField(source="offer.destination", read_only=True)
    applicant_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    # Add comment serialization (read-only)
    comments = PilgrimageVisaApplicationCommentSerializer(many=True, read_only=True)

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
            "preferred_travel_date",
            "group_travel",
            "passport_photo",
            "medical_certificate",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            "status",
            "status_display",
            "created_at",
            "updated_at",
            "comments",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "offer_title",
            "destination",
            "applicant_name",
            "status_display",
            "comments",
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

    def get_status_display(self, obj):
        if hasattr(obj, "status_display"):
            return obj.status_display
        return None


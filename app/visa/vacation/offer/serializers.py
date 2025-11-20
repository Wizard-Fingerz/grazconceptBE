from rest_framework import serializers
from .models import (
    VacationOffer,
    VacationOfferIncludedItem,
    VacationOfferImage,
    VacationVisaApplication,
)
from django_countries.serializers import CountryFieldMixin
from definition.models import TableDropDownDefinition
from account.client.models import Client

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

# ---- Vacation Visa Application Serializer ----

class VacationVisaApplicationSerializer(CountryFieldMixin, serializers.ModelSerializer):
    # Display applicant info and offer info if required
    applicant = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    offer = serializers.PrimaryKeyRelatedField(queryset=VacationOffer.objects.all())
    status = serializers.PrimaryKeyRelatedField(
        queryset=TableDropDownDefinition.objects.filter(
            table_name='vacation_application_status',
            is_active=True
        ),
        required=False,
        allow_null=True,
        default=None
    )
    # Fix: remove redundant source kwarg per DRF error (source='status_display' is unnecessary)
    status_display = serializers.CharField(read_only=True)

    class Meta:
        model = VacationVisaApplication
        fields = [
            'id',
            'offer',
            'applicant',
            'passport_number',
            'date_of_birth',
            # 'destination',
            'travel_date',
            'number_of_people',
            'accommodation_type',
            'identification_document',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            'status',
            'status_display',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status_display']

    def create(self, validated_data):
        # The model handles default 'Draft' status if status not provided,
        # but you can enforce it here as well
        if 'status' not in validated_data or validated_data['status'] is None:
            try:
                draft_status = TableDropDownDefinition.objects.filter(
                    table_name='vacation_application_status',
                    is_active=True,
                    term="Draft"
                ).first()
                validated_data['status'] = draft_status
            except Exception:
                validated_data['status'] = None
        return super().create(validated_data)

    def to_representation(self, instance):
        """
        Optionally, override to add more details (e.g., applicant/basic offer data).
        """
        rep = super().to_representation(instance)
        # Add applicant info (limited to username & id for privacy)
        rep['applicant_detail'] = {
            'id': instance.applicant.id,
            'name': getattr(instance.applicant, 'get_full_name', lambda: None)() or getattr(instance.applicant.user, 'username', None)
        } if instance.applicant else None
        # Add offer title for quick reference
        rep['offer_title'] = instance.offer.title if instance.offer else None
        return rep

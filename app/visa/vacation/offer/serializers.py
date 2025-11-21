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
        Customize representation to avoid AttributeError if Client has no user.
        Populate applicant_detail with id and either get_full_name(), username (if applicant has .user), or email (if available).
        """
        rep = super().to_representation(instance)
        applicant_detail = None
        if instance.applicant:
            # Try get_full_name if exists and returns a value
            name = None
            get_full_name = getattr(instance.applicant, 'get_full_name', None)
            if callable(get_full_name):
                name = get_full_name()
            if not name:
                # Try .user.username if applicant has a user and user has username field
                user = getattr(instance.applicant, 'user', None)
                if user and hasattr(user, 'username'):
                    name = user.username
            if not name:
                # Fallback: try email field
                name = getattr(instance.applicant, 'email', None)
            applicant_detail = {
                'id': instance.applicant.id,
                'name': name
            }
        rep['applicant_detail'] = applicant_detail
        rep['offer_title'] = instance.offer.title if instance.offer else None
        return rep

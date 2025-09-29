from rest_framework import serializers
from app.visa.work.offers.models import WorkVisaOffer
from app.visa.work.organization.serializers import WorkOrganizationSerializer

class WorkVisaOfferSerializer(serializers.ModelSerializer):
    organization = WorkOrganizationSerializer(read_only=True)
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkVisaOffer._meta.get_field('organization').remote_field.model.objects.all(),
        source='organization',
        write_only=True
    )

    class Meta:
        model = WorkVisaOffer
        fields = [
            'id',
            'organization',
            'organization_id',
            'job_title',
            'job_description',
            'country',
            'city',
            'salary',
            'currency',
            'start_date',
            'end_date',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

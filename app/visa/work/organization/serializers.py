from rest_framework import serializers
from .models import WorkOrganization

class WorkOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrganization
        fields = [
            'id',
            'name',
            'registration_number',
            'address',
            'country',
            'city',
            'website',
            'contact_email',
            'contact_phone',
            'is_active',
            'created_at',
            'updated_at',
        ]

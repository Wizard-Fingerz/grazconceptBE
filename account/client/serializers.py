from rest_framework import serializers
from .models import Client
from django.contrib.auth.hashers import make_password

class ClientSerializer(serializers.ModelSerializer):
    client_type_name = serializers.ReadOnlyField()
    service_of_interest_name = serializers.ReadOnlyField()
    assigned_to_teams_name = serializers.ReadOnlyField()
    country = serializers.CharField(allow_blank=True, allow_null=True, required=False)

    class Meta:
        model = Client
        fields = [
            'id',
            'password',
            'last_login',
            'is_superuser',
            'first_name',
            'last_name',
            'email',
            'country',
            'is_staff',
            'is_active',
            'user_type',
            'created_by',
            'client_type',
            'service_of_interest',
            'assign_to_teams',
            'internal_note_and_reminder',
            'client_type_name',
            'service_of_interest_name',
            'assigned_to_teams_name',
            "is_prospect"
        ]
        read_only_fields = [
            'id',
            'last_login',
            'is_superuser',
            'is_staff',
            'is_active',
            'created_by',
            'client_type_name',
            'service_of_interest_name',
            'assigned_to_teams_name',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure country is always a string or None, not a Country object
        country = getattr(instance, 'country', None)
        if hasattr(country, 'code'):
            data['country'] = str(country)
        elif country is not None:
            data['country'] = str(country)
        else:
            data['country'] = None
        return data

    def create(self, validated_data):
        password = validated_data.get('password')
        if password:
            validated_data['password'] = make_password(password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.get('password')
        if password:
            validated_data['password'] = make_password(password)
        return super().update(instance, validated_data)

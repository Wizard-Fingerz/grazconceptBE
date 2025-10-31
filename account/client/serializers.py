from rest_framework import serializers

from wallet.serializers import WalletSerializer
from .models import Client
from django.contrib.auth.hashers import make_password

class ClientSerializer(serializers.ModelSerializer):
    client_type_name = serializers.ReadOnlyField()
    service_of_interest_name = serializers.ReadOnlyField()
    assigned_to_teams_name = serializers.ReadOnlyField()
    country = serializers.SerializerMethodField()
    wallet = WalletSerializer()

    class Meta:
        model = Client
        fields = [
            'id',
            'password',
            'last_login',
            'is_superuser',
            'first_name',
            'middle_name',
            'last_name',
            'phone_number',
            'date_of_birth',
            'gender',
            'current_address',
            'country_of_residence',
            'nationality',
            'profile_picture',
            'email',
            'country',
            'is_staff',
            'is_active',
            'user_type',
            'created_by',
            'client_type',
            'partner_type',
            'service_of_interest',
            'assign_to_teams',
            'internal_note_and_reminder',
            'client_type_name',
            'service_of_interest_name',
            'assigned_to_teams_name',
            "is_prospect",
            "wallet",

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
            "wallet",
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_country(self, obj):
        # Return the full country name if available, else None
        country = getattr(obj, 'country', None)
        if country:
            # If it's a django_countries Country object, use .name
            name = getattr(country, 'name', None)
            if name:
                return name
            # If it's a string code, try to get the name from django_countries
            try:
                from django_countries import countries
                return dict(countries).get(str(country), str(country))
            except ImportError:
                return str(country)
        return None

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

from rest_framework import serializers

from wallet.serializers import WalletSerializer
from .models import Client
from django.contrib.auth.hashers import make_password


class ClientSerializer(serializers.ModelSerializer):
    client_type_name = serializers.ReadOnlyField()
    service_of_interest_name = serializers.ReadOnlyField()
    assigned_to_teams_name = serializers.ReadOnlyField()

    country = serializers.SerializerMethodField()
    country_of_residence = serializers.SerializerMethodField()
    nationality = serializers.SerializerMethodField()

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
            "referred_by",
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
        value = obj.country
        if not value:
            return None
        return {"code": value.code, "name": value.name}

    def get_country_of_residence(self, obj):
        value = getattr(obj, "country_of_residence", None)
        if not value:
            return {"code": None, "name": None}
        return {"code": value.code, "name": value.name}

    def get_nationality(self, obj):
        value = getattr(obj, "nationality", None)
        if not value:
            return {"code": None, "name": None}
        return {"code": value.code, "name": value.name}

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

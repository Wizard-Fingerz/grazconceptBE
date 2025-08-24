from rest_framework import serializers
from .models import Client

from django.contrib.auth.hashers import make_password

class ClientSerializer(serializers.ModelSerializer):
    client_type_name = serializers.ReadOnlyField()
    service_of_interest_name = serializers.ReadOnlyField()
    assigned_to_teams_name = serializers.ReadOnlyField()

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
        ]
        read_only_fields = [
            'id',
            'last_login',
            'is_superuser',
            'is_staff',
            'is_active',
            'date_joined',
            'created_by',
            'client_type_name',
            'service_of_interest_name',
            'assigned_to_teams_name',
        ]

    def create(self, validated_data):
        # Hash the password before creating the Client instance
        password = validated_data.get('password')
        if password:
            validated_data['password'] = make_password(password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Hash the password if it's being updated
        password = validated_data.get('password')
        if password:
            validated_data['password'] = make_password(password)
        return super().update(instance, validated_data)

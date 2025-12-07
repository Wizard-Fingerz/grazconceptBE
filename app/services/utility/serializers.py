from rest_framework import serializers
from .models import UtilityProvider, UtilityBillPayment

class UtilityProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilityProvider
        fields = ['id', 'label', 'value', 'logo', 'accent']

class UtilityBillPaymentSerializer(serializers.ModelSerializer):
    provider = UtilityProviderSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=UtilityProvider.objects.all(),
        source='provider',
        write_only=True
    )

    class Meta:
        model = UtilityBillPayment
        fields = [
            'id',
            'user',
            'provider',
            'provider_id',
            'meter_type',
            'meter_number',
            'amount',
            'status',
            'transaction_reference',
            'token',
            'created_at',
            'completed_at',
            'error_message',
        ]
        read_only_fields = [
            'id',
            'user',
            'status',
            'token',
            'created_at',
            'completed_at',
            'error_message',
            'transaction_reference',
        ]

from rest_framework import serializers
from .models import EducationFeeProvider, EducationFeeType, EducationFeePayment

class EducationFeeProviderSerializer(serializers.ModelSerializer):
    key = serializers.StringRelatedField()

    class Meta:
        model = EducationFeeProvider
        fields = [
            'id',
            'key',
            'label',
            'logo_url',
            'color',
        ]


class EducationFeeTypeSerializer(serializers.ModelSerializer):
    provider = EducationFeeProviderSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=EducationFeeProvider.objects.all(),
        write_only=True,
        source='provider'
    )

    class Meta:
        model = EducationFeeType
        fields = [
            'id',
            'provider',
            'provider_id',
            'value',
            'label',
            'min_amount',
            'max_amount',
            'default_amount',
        ]


class EducationFeePaymentSerializer(serializers.ModelSerializer):
    provider = EducationFeeProviderSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=EducationFeeProvider.objects.all(),
        write_only=True,
        source='provider'
    )
    fee_type = EducationFeeTypeSerializer(read_only=True)
    fee_type_id = serializers.PrimaryKeyRelatedField(
        queryset=EducationFeeType.objects.all(),
        write_only=True,
        source='fee_type'
    )
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = EducationFeePayment
        fields = [
            'id',
            'user',
            'provider',
            'provider_id',
            'fee_type',
            'fee_type_id',
            'candidate_name',
            'reg_no',
            'amount',
            'transaction_ref',
            'status',
            'created_at',
            'paid_at',
        ]
        read_only_fields = ['id', 'created_at', 'paid_at', 'status']


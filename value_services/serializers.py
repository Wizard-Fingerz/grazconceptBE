from rest_framework import serializers
from .models import CableTVSubscription, BillPaymentRecord


class CableTVSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CableTVSubscription
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'status', 'transaction_reference', 'flw_tx_ref',
            'flw_transaction_id', 'provider_reference', 'error_message',
            'meta', 'created_at', 'completed_at',
        ]


class BillPaymentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillPaymentRecord
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'status', 'transaction_reference', 'flw_tx_ref',
            'flw_transaction_id', 'provider_reference', 'token',
            'error_message', 'meta', 'created_at', 'completed_at',
        ]


# ── Request serializers ──────────────────────────────────────────────────────

class ElectricityPayRequestSerializer(serializers.Serializer):
    provider = serializers.CharField()          # e.g. "ikeja-electric"
    meter_type = serializers.ChoiceField(choices=['prepaid', 'postpaid'])
    meter_number = serializers.CharField(max_length=30)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=500)
    payment_method = serializers.ChoiceField(
        choices=['wallet', 'card', 'bank_transfer', 'mobile_money'],
        default='wallet',
    )


class CableRenewRequestSerializer(serializers.Serializer):
    provider = serializers.CharField()          # e.g. "dstv"
    provider_label = serializers.CharField()
    package_code = serializers.CharField()
    package_label = serializers.CharField()
    iuc_number = serializers.CharField(max_length=30)
    account_name = serializers.CharField(required=False, allow_blank=True, default='')
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=100)
    payment_method = serializers.ChoiceField(
        choices=['wallet', 'card', 'bank_transfer', 'mobile_money'],
        default='wallet',
    )


class EducationFeePayRequestSerializer(serializers.Serializer):
    provider = serializers.CharField()          # e.g. "waec"
    provider_label = serializers.CharField()
    fee_type = serializers.CharField()          # e.g. "waec-registration"
    fee_type_label = serializers.CharField()
    candidate_name = serializers.CharField(required=False, allow_blank=True, default='')
    reg_no = serializers.CharField(required=False, allow_blank=True, default='')
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=100)
    payment_method = serializers.ChoiceField(
        choices=['wallet', 'card', 'bank_transfer', 'mobile_money'],
        default='wallet',
    )

from rest_framework import serializers
from .models import PaymentGateway, PaymentGatewayCallbackLog

class PaymentGatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGateway
        fields = [
            'id',
            'name',
            'is_active',
            'credentials',
        ]

class PaymentGatewayCallbackLogSerializer(serializers.ModelSerializer):
    payment_gateway = PaymentGatewaySerializer(read_only=True)
    wallet_transaction = serializers.SerializerMethodField()

    class Meta:
        model = PaymentGatewayCallbackLog
        fields = [
            'id',
            'payment_gateway',
            'payload',
            'received_at',
            'processed',
            'wallet_transaction',
        ]

    def get_wallet_transaction(self, obj):
        tx = obj.wallet_transaction
        if tx:
            return {
                "id": tx.id,
                "reference": tx.reference,
                "amount": tx.amount,
                "currency": tx.currency,
                "status": tx.status,
            }
        return None

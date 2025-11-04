from rest_framework import serializers
from .models import WalletTransaction

class WalletTransactionSerializer(serializers.ModelSerializer):
    wallet = serializers.StringRelatedField(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    payment_gateway = serializers.StringRelatedField(read_only=True)
    savings_plan = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = WalletTransaction
        fields = [
            'id',
            'user',
            'wallet',
            'transaction_type',
            'amount',
            'currency',
            'description',
            'status',
            'reference',
            'payment_gateway',
            'meta',
            'created_at',
            'updated_at',
            'savings_plan',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'wallet', 'reference']

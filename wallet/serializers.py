from rest_framework import serializers
from .models import Wallet

class WalletSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Wallet
        fields = [
            'id',
            'user',
            'balance',
            'currency',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

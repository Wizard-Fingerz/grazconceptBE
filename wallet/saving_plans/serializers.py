from rest_framework import serializers
from .models import SavingsPlan

class SavingsPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsPlan
        fields = [
            'id',
            'user',
            'wallet',
            'name',
            'target_amount',
            'amount_saved',
            'currency',
            'start_date',
            'end_date',
            'is_recurring',
            'recurrence_period',
            'status',
            'created_at',
            'updated_at',
            'meta',
        ]
        read_only_fields = ('id', 'amount_saved', 'created_at', 'updated_at')


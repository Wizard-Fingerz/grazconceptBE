from rest_framework import serializers
from .models import LoanApplication, LoanRepayment

class LoanApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplication
        fields = [
            'id',
            'user',
            'amount',
            'currency',
            'purpose',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

class LoanRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRepayment
        fields = [
            'id',
            'loan_application',
            'user',
            'amount',
            'currency',
            'payment_date',
            'reference',
        ]
        read_only_fields = ['id', 'payment_date']

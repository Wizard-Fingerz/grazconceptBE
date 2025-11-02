from rest_framework import serializers
from .models import LoanApplication, LoanRepayment, LoanOffer

class LoanOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanOffer
        fields = [
            'id',
            'loan_type',
            'name',
            'description',
            'min_amount',
            'max_amount',
            'currency',
            'required_documents',
            'requirements',
            'interest_rate',
            'duration_months',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]

class LoanApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplication
        fields = [
            'id',
            'user',
            'loan_offer',
            'amount',
            'currency',
            'purpose',
            'status',
            'filled_details',
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

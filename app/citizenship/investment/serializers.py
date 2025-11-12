from rest_framework import serializers
from .models import InvestmentPlan, InvestmentPlanBenefit, Investment

class InvestmentPlanBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentPlanBenefit
        fields = [
            'id',
            'plan',
            'text',
            'order',
        ]
        read_only_fields = ['id', 'plan']

class InvestmentPlanSerializer(serializers.ModelSerializer):
    benefits = InvestmentPlanBenefitSerializer(many=True, read_only=True)

    class Meta:
        model = InvestmentPlan
        fields = [
            'id',
            'name',
            'description',
            'price',
            'roi_percentage',
            'period_months',
            'color',
            'progress',
            'withdraw_available',
            'warning_note',
            'docs_url',
            'benefits',
        ]
        read_only_fields = ['id', 'progress', 'withdraw_available']

class InvestmentSerializer(serializers.ModelSerializer):
    plan = InvestmentPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=InvestmentPlan.objects.all(), source='plan', write_only=True
    )
    status_name = serializers.CharField(source='status_name', read_only=True)
    is_matured = serializers.BooleanField(source='is_matured', read_only=True)
    can_withdraw = serializers.BooleanField(source='can_withdraw', read_only=True)
    formatted_period = serializers.CharField(source='formatted_period', read_only=True)

    class Meta:
        model = Investment
        fields = [
            'id',
            'investor',
            'plan',
            'plan_id',
            'amount',
            'roi_amount',
            'start_date',
            'maturity_date',
            'created_at',
            'withdrawable',
            'next_withdraw_date',
            'status',
            'status_name',
            'is_matured',
            'can_withdraw',
            'formatted_period',
        ]
        read_only_fields = [
            'id',
            'roi_amount',
            'created_at',
            'is_matured',
            'can_withdraw',
            'formatted_period',
            'status_name',
        ]

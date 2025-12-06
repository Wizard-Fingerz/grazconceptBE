from rest_framework import serializers
from .models import NetworkProvider, AirtimePurchase, DataPlan, DataPurchase

class NetworkProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkProvider
        fields = [
            "id",
            "value",
            "label",
            "logo",
            "accent",
            "active",
        ]


class AirtimePurchaseSerializer(serializers.ModelSerializer):
    provider = NetworkProviderSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=NetworkProvider.objects.filter(active=True),
        write_only=True,
        source="provider",
    )

    class Meta:
        model = AirtimePurchase
        fields = [
            "id",
            "user",
            "provider",
            "provider_id",
            "phone",
            "amount",
            "created_at",
            "completed",
            "external_ref",
            "status_message",
        ]
        read_only_fields = (
            "id", "created_at", "completed", "external_ref", "status_message", "user", "provider"
        )

    def create(self, validated_data):
        # The 'user' field should be set in the view using serializer.save(user=request.user)
        return super().create(validated_data)


class DataPlanSerializer(serializers.ModelSerializer):
    provider = NetworkProviderSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=NetworkProvider.objects.filter(active=True),
        write_only=True,
        source="provider",
    )

    class Meta:
        model = DataPlan
        fields = [
            "id",
            "provider",
            "provider_id",
            "label",
            "value",
            "category",
            "data",
            "amount",
            "logo",
            "accent",
        ]


class DataPurchaseSerializer(serializers.ModelSerializer):
    provider = NetworkProviderSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=NetworkProvider.objects.filter(active=True),
        write_only=True,
        source="provider",
    )
    plan = DataPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=DataPlan.objects.all(),
        write_only=True,
        source="plan",
    )

    class Meta:
        model = DataPurchase
        fields = [
            "id",
            "user",
            "provider",
            "provider_id",
            "plan",
            "plan_id",
            "phone",
            "amount",
            "created_at",
            "completed",
            "external_ref",
            "status_message",
        ]
        read_only_fields = (
            "id", "created_at", "completed", "external_ref", "status_message", "user", "provider", "plan"
        )

    def create(self, validated_data):
        # The 'user' field should be set in the view using serializer.save(user=request.user)
        return super().create(validated_data)

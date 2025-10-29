from rest_framework import serializers
from .models import EuropeanCitizenshipOffer, InvestmentOption


class InvestmentOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentOption
        fields = [
            "id",
            "type",
            "min_amount",
            "amount_field",
            "amount_label",
        ]


class EuropeanCitizenshipOfferSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()
    investment_options = InvestmentOptionSerializer()

    class Meta:
        model = EuropeanCitizenshipOffer
        fields = [
            "id",
            "country",
            "quote",
            "type",
            "description",
            "minimum_investment",
            "visa_free_access",
            "dual_citizenship",
            "requirements",
            "processing_time",
            "government_fees",
            "family_inclusion",
            "benefits",
            "flag_url",
            "gradient",
            "created_at",
            "updated_at",
            "investment_options",
        ]

    def get_country(self, obj):
        # Return both the country code and name
        return {
            "code": obj.country.code if hasattr(obj.country, "code") else str(obj.country),
            "name": obj.country.name if hasattr(obj.country, "name") else str(obj.country)
        }

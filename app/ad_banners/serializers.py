from rest_framework import serializers
from .models import AdBanner

class AdBannerSerializer(serializers.ModelSerializer):
    is_currently_active = serializers.SerializerMethodField()

    class Meta:
        model = AdBanner
        fields = [
            'id',
            'title',
            'image',
            'link_url',
            'position',
            'is_active',
            'start_date',
            'end_date',
            'created_at',
            'updated_at',
            'is_currently_active',
        ]

    def get_is_currently_active(self, obj):
        return obj.is_currently_active()

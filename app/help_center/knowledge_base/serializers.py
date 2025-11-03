from rest_framework import serializers
from .models import FaqArticle

class FaqArticleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.term', read_only=True)

    class Meta:
        model = FaqArticle
        fields = [
            'id',
            'question',
            'answer',
            'category',
            'category_name',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'category_name')

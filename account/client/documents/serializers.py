from rest_framework import serializers
from .models import ClientDocuments

class ClientDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientDocuments
        fields = [
            'id',
            'client',
            'file',
            'type',
            'uploaded_at',
            'uploaded_by',
            'type_term'
        ]
        read_only_fields = [
            'id',
            'uploaded_at',
            'type_term'
        ]

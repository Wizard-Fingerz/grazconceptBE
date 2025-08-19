from rest_framework.serializers import ModelSerializer
from .models import TableDropDownDefinition

class TableDropDownDefinitionSerializer(ModelSerializer):
    class Meta:
        model = TableDropDownDefinition
        fields = ( "id", "term", "table_name", "is_active", "is_system_defined")
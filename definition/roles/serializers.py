from .models import Roles
from rest_framework.serializers import ModelSerializer
from ..permissions.serializers import PermissionSerializer, ModulesSerializer

class BaseRoleSerializer(ModelSerializer):
    class Meta:
        model = Roles
        fields = ('id', 'name', 'is_active', 'modules', 'custom_id')

class DetailedRoleSerializer(ModelSerializer):
    #permissions = PermissionSerializer(many=True, read_only=True)
    modules = ModulesSerializer(many=True, read_only=True)

    class Meta:
        model = Roles
        fields = ('id', 'name', 'is_active', 'modules', 'custom_id')

class RoleModulesSerializer(ModelSerializer):
    class Meta:
        model = Roles
        fields = ['id', 'modules', 'custom_id']

#class RolePermissionSerializer(ModelSerializer):
#    class Meta:
#        model = Roles
#        fields = ['id', 'permissions']
#
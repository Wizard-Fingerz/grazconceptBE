from rest_framework import serializers
from .models import UserPermissions, Modules

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPermissions
        fields = ['id', 'name']


class ModulesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modules
        fields = ['id', 'name', 'permissions']


class ModuleWithPermissionsSerializer(serializers.Serializer):
    module = ModulesSerializer()
    permissions = PermissionSerializer(many=True)

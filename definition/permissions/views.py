from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from django.contrib.auth.models import Permission
# from ..roles.models import Roles
from .serializers import PermissionSerializer, ModulesSerializer
from .models import UserPermissions
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination
from .models import Modules
from rest_framework.views import APIView
from .serializers import ModuleWithPermissionsSerializer
from rest_framework.filters import SearchFilter


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 15

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'num_pages': self.page.paginator.num_pages,
            'page_size': self.page_size,
            'current_page': self.page.number,
            'results': data
        })


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = UserPermissions.objects.all().order_by('-created_at')
    serializer_class = PermissionSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [ SearchFilter]
    filterset_fields = ['name', 'id']
    search_fields = ['name', 'id']

    # parser_classes = [FormParser, MultiPartParser]


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Modules.objects.all().order_by('-created_at')
    serializer_class = ModulesSerializer
    pagination_class = CustomPageNumberPagination
    
    # parser_classes = [FormParser, MultiPartParser]

class ModuleWithPermissionsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        modules = Modules.objects.all().order_by('-created_at')
        serialized_data = []
        
        for module in modules:
            #permissions = UserPermissions.objects.filter(module=module)
            permissions = module.permissions.all()
            serialized_module = ModuleWithPermissionsSerializer({
                'module': module,
                'permissions': permissions
            }).data
            serialized_data.append(serialized_module)

        return Response(serialized_data)


# class PermissionDeleteView(viewsets.ViewSet,generics.DestroyAPIView):
#     queryset = UserPermissions.objects.all()
#     serializer_class = PermissionSerializer
#     parser_classes = [FormParser, MultiPartParser]

# class PermissionUpdateView(viewsets.ViewSet,generics.UpdateAPIView):
#     queryset = UserPermissions.objects.all()
#     serializer_class = PermissionSerializer
#     parser_classes = [FormParser, MultiPartParser]




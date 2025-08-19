from rest_framework import viewsets, generics, status
from rest_framework.pagination import PageNumberPagination
from .serializers import BaseRoleSerializer, DetailedRoleSerializer, RoleModulesSerializer
from .models import Roles, UserPermissions, Modules
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
#from .roles_permissions import CanCreateRoles, CanDeleteRoles, CanUpdateRoles
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import HttpResponse
import csv
from django.db.models.fields.files import FieldFile


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

class RoleViewSet(viewsets.ModelViewSet):

    #queryset = Roles.objects.all().order_by('-created_at')
    queryset = Roles.objects.filter(is_deleted=False).order_by('-created_at')
    pagination_class = CustomPageNumberPagination 
    lookup_field = 'custom_id'
    # parser_classes = [FormParser, MultiPartParser]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return DetailedRoleSerializer
        return BaseRoleSerializer

    #def get_permissions(self):
    #    if self.action == 'create':
    #        return [IsAuthenticated(), CanCreateRoles()]
    #    elif self.action in ['update', 'partial_update']:
    #        return [IsAuthenticated(), CanUpdateRoles()]
    #    elif self.action in ['list', 'retrieve']:
    #        return [IsAuthenticatedOrReadOnly()]
    #    elif self.action == 'destroy':
    #        return [IsAuthenticated(), CanDeleteRoles()]
    #    return [IsAuthenticated()]

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'features': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='List of feature IDs to be associated with the role'
                )
            },
            required=['features'],
            title='Update Role Features'
        ),
        responses={
            200: openapi.Response('Features updated successfully'),
            400: 'Bad Request',
            404: 'Role not found',
        }
    )
    
    @action(detail=True, methods=['post'])
    def update_features(self, request, pk=None):
        role = self.get_object()
        features = request.data.get('features', [])
        role.accessible_features.set(Feature.objects.filter(id__in=features))
        return Response({'status': 'features updated'})
    
    @action(detail=False, methods=['get'], url_path='export-csv')
    def export_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Roles.csv"'

        # Create a CSV writer
        writer = csv.writer(response)

        model = Roles
        fields = [field.name for field in model._meta.fields]

        writer.writerow(fields)

        orgs = model.objects.all()
        for obj in orgs:
            row = []
            for field in fields:
                value = getattr(obj, field)
                if isinstance(value, FieldFile):  
                    value = value.url if value and hasattr(value, 'url') else ''
                row.append(value)
            writer.writerow(row)

        return response
    
    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request):
        if 'file' not in request.FILES:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        created_groups = []
        errors = []

        def normalize(value):
            return value.strip().lower() if value else None

        for row in reader:
            if not row.get('name'):
                errors.append({'row': row, 'error': 'Name is required'})
                continue

            row_data = {
                'name': row['name'],
                'is_active': False,
            }

            serializer = BaseRoleSerializer(data=row_data)
            if serializer.is_valid():
                drug = serializer.save()
                created_groups.append(drug)
            else:
                errors.append({'row': row, 'error': serializer.errors})

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'message': f'{len(created_groups)} Role(s) created successfully'},
            status=status.HTTP_201_CREATED
        )
    


class AttachRoleWithModulesAPIView(APIView):
    #permission_classes = [CanCreateRoles, CanUpdateRoles]
    
    @swagger_auto_schema(request_body=RoleModulesSerializer, responses={200: 'Success', 400: 'Bad Request'})
    def post(self, request, role_id):
        if self.request.user.is_authenticated:
            role = Roles.objects.get(pk=role_id)
            module_ids = request.data.get('modules', [])
            modules = Modules.objects.filter(pk__in=module_ids)
            role.modules.add(*modules)
            serializer = RoleModulesSerializer(role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'This route can only be accessed by users with permissions'}, status=status.HTTP_401_UNAUTHORIZED)


class RoleDownloadCSVView(APIView):
    #permission_classes = [IsAuthenticated] 

    def get(self, request, *args, **kwargs):
        
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="roles.csv"'},
        )

        writer = csv.writer(response)
        
        # Write the header row
        writer.writerow([
            "name", "is_active",
        ])
        
        # Optionally, you can add example data rows
        example_data = [
            [ "Human Resources", True],
            [ "role test", True],
            [ "role test", True],
        ]
        
        for row in example_data:
            writer.writerow(row)

        return response 


class RoleBulkCreateView(APIView):
    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        created_groups = []
        errors = []

        def normalize(value):
            return value.strip().lower() if value else None

        for row in reader:
            if not row.get('name'):
                errors.append({'row': row, 'error': 'Name is required'})
                continue

            row_data = {
                'name': row['name'],
                'is_active': False,
            }

            serializer = BaseRoleSerializer(data=row_data)
            if serializer.is_valid():
                drug = serializer.save()
                created_groups.append(drug)
            else:
                errors.append({'row': row, 'error': serializer.errors})

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'message': f'{len(created_groups)} Role(s) created successfully'},
            status=status.HTTP_201_CREATED
        )
    

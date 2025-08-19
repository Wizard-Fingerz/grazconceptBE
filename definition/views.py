from rest_framework.permissions import AllowAny
from rest_framework.decorators import action, permission_classes
from rest_framework import viewsets, pagination, status
from rest_framework.response import Response
from rest_framework.decorators import action  # ✅ Needed for @action

from definition.serializers import TableDropDownDefinitionSerializer
from .models import TableDropDownDefinition
from rest_framework.permissions import AllowAny, IsAuthenticated


class CustomPagination(pagination.PageNumberPagination):
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


class TableDropDownDefinitionViewSet(viewsets.ModelViewSet):
    queryset = TableDropDownDefinition.objects.all().order_by('-created_at')
    serializer_class = TableDropDownDefinitionSerializer
    pagination_class = CustomPagination
    lookup_field = 'id'

    def get_permissions(self):
        if self.action == 'get_by_table_name':
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='by-table-name')
    def get_by_table_name(self, request):
        table_name = request.query_params.get('table_name')
        if not table_name:
            return Response({"error": "Missing 'table_name' query parameter"}, status=400)

        filtered_qs = self.queryset.filter(table_name=table_name)
        page = self.paginate_queryset(filtered_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(filtered_qs, many=True)
        return Response(serializer.data)

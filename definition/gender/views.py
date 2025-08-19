from rest_framework import viewsets, pagination
from .models import Gender
from ..serializers import GenderSerializer
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .gender_permissions import CanCreateGender, CanDeleteGender, CanUpdateGender
from rest_framework.response import Response

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

class GenderViewSet(viewsets.ModelViewSet):
    queryset = Gender.objects.all().order_by('-created_at')
    serializer_class = GenderSerializer
    # parser_classes = [ FormParser, MultiPartParser]
    pagination_class = CustomPagination
    lookup_field = 'custom_id'

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateGender()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), CanUpdateGender()]
        elif self.action in ['list', 'retrieve']:
            return [IsAuthenticatedOrReadOnly()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), CanDeleteGender()]
        return [IsAuthenticated()]
    
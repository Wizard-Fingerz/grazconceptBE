from rest_framework import viewsets

from app.views import CustomPagination

from .models import ProgramType, Institution, CourseOfStudy
from .serializers import (
    # CountrySerializer,
    # CitySerializer,
    ProgramTypeSerializer,
    InstitutionSerializer,
    CourseOfStudySerializer,
)

# class CountryViewSet(viewsets.ModelViewSet):
#     queryset = Country.objects.all()
#     serializer_class = CountrySerializer

# class CityViewSet(viewsets.ModelViewSet):
#     queryset = City.objects.all()
#     serializer_class = CitySerializer

class ProgramTypeViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    queryset = ProgramType.objects.all()
    serializer_class = ProgramTypeSerializer

class InstitutionViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer

    def get_paginate_by(self, request):
        # Deprecated, but here for Django compatibility; not used in DRF
        return 100

    def get_page_size(self, request):
        # Not called by DRF, but placed here for completeness
        return 100

    def get_queryset(self):
        # No custom filtering; return all as in original
        return super().get_queryset()

    def paginate_queryset(self, queryset):
        """
        Override to force the page size to 100 regardless of the query param.
        """
        # Set the page_size before calling DRF's built-in pagination
        self.pagination_class.page_size = 100
        return super().paginate_queryset(queryset)

    def get_pagination_class(self):
        """
        Optionally override pagination class to always use a page size of 100.
        """
        class CustomPageSize100(CustomPagination):
            page_size = 100
            max_page_size = 100
            page_size_choices = [100]

            def get_page_size(self, request):
                return 100

        return CustomPageSize100

    def get_serializer_class(self):
        return self.serializer_class



class CourseOfStudyViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    queryset = CourseOfStudy.objects.all()
    serializer_class = CourseOfStudySerializer

    def get_paginate_by(self, request):
        # Deprecated, but here for Django compatibility; not used in DRF
        return 100

    def get_page_size(self, request):
        # Not called by DRF, but placed here for completeness
        return 100

    def get_queryset(self):
        # No custom filtering; return all as in original
        return super().get_queryset()

    def paginate_queryset(self, queryset):
        """
        Override to force the page size to 100 regardless of the query param.
        """
        # Set the page_size before calling DRF's built-in pagination
        self.pagination_class.page_size = 100
        return super().paginate_queryset(queryset)

    def get_pagination_class(self):
        """
        Optionally override pagination class to always use a page size of 100.
        """
        class CustomPageSize100(CustomPagination):
            page_size = 100
            max_page_size = 100
            page_size_choices = [100]

            def get_page_size(self, request):
                return 100

        return CustomPageSize100


    def get_queryset(self):
        """
        Optionally restricts the returned CourseOfStudy objects by filtering against
        query parameters in the URL. Supports 'limit' param for limiting results.
        The filters expect IDs as input.
        """
        queryset = super().get_queryset()
        program_type = self.request.query_params.get('program_type')
        institution = self.request.query_params.get('institution')
        limit = self.request.query_params.get('limit')

        if program_type:
            try:
                program_type_id = int(program_type)
                queryset = queryset.filter(program_type_id=program_type_id)
            except (ValueError, TypeError):
                pass  # Ignore invalid ids
        if institution:
            try:
                institution_id = int(institution)
                queryset = queryset.filter(institution_id=institution_id)
            except (ValueError, TypeError):
                pass  # Ignore invalid ids
        if limit is not None:
            try:
                limit_value = int(limit)
                if limit_value > 0:
                    queryset = queryset[:limit_value]
            except (ValueError, TypeError):
                pass  # Ignore invalid limit values
        return queryset


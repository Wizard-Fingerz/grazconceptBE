from rest_framework import viewsets

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
    queryset = ProgramType.objects.all()
    serializer_class = ProgramTypeSerializer

class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer

class CourseOfStudyViewSet(viewsets.ModelViewSet):
    queryset = CourseOfStudy.objects.all()
    serializer_class = CourseOfStudySerializer


    def get_queryset(self):
        """
        Optionally restricts the returned offers by filtering against
        query parameters in the URL. Supports 'limit' param for limiting results.
        """
        queryset = super().get_queryset()
        program_type = self.request.query_params.get('program_type')
        institution = self.request.query_params.get('institution')
        limit = self.request.query_params.get('limit')

        if program_type:
            queryset = queryset.filter(program_type=program_type)
        if institution:
            queryset = queryset.filter(institution=institution)
        if limit is not None:
            try:
                limit_value = int(limit)
                if limit_value > 0:
                    queryset = queryset[:limit_value]
            except (ValueError, TypeError):
                pass  # Ignore invalid limit values
        return queryset


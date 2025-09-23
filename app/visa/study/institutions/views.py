from rest_framework import viewsets

from .models import Country, City, ProgramType, Institution, CourseOfStudy
from .serializers import (
    CountrySerializer,
    CitySerializer,
    ProgramTypeSerializer,
    InstitutionSerializer,
    CourseOfStudySerializer,
)

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer

class ProgramTypeViewSet(viewsets.ModelViewSet):
    queryset = ProgramType.objects.all()
    serializer_class = ProgramTypeSerializer

class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer

class CourseOfStudyViewSet(viewsets.ModelViewSet):
    queryset = CourseOfStudy.objects.all()
    serializer_class = CourseOfStudySerializer


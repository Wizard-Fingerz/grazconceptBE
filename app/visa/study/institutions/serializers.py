

from rest_framework import serializers
from .models import Country, City, ProgramType, Institution, CourseOfStudy

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']

class CitySerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source='country', write_only=True
    )

    class Meta:
        model = City
        fields = ['id', 'name', 'country', 'country_id']

class ProgramTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramType
        fields = ['id', 'name', 'description']

class InstitutionSerializer(serializers.ModelSerializer):
    program_types = ProgramTypeSerializer(many=True, read_only=True)
    program_type_ids = serializers.PrimaryKeyRelatedField(
        queryset=ProgramType.objects.all(), source='program_types', many=True, write_only=True, required=False
    )

    class Meta:
        model = Institution
        fields = [
            'id', 'name', 'country', 'city', 
            'email_address', 'address', 'website', 'program_types', 'program_type_ids'
        ]

class CourseOfStudySerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    institution_id = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(), source='institution', write_only=True
    )
    program_type = ProgramTypeSerializer(read_only=True)
    program_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ProgramType.objects.all(), source='program_type', write_only=True
    )

    class Meta:
        model = CourseOfStudy
        fields = [
            'id', 'name', 'description', 'institution', 'institution_id',
            'program_type', 'program_type_id'
        ]

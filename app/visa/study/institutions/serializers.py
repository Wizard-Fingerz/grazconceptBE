from rest_framework import serializers
from .models import ProgramType, Institution, CourseOfStudy

class ProgramTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramType
        fields = ['id', 'name', 'description']

class CourseOfStudySerializer(serializers.ModelSerializer):
    # For nested use in InstitutionSerializer, don't nest institution/program_type to avoid recursion
    class Meta:
        model = CourseOfStudy
        fields = [
            'id', 'name', 'description', 'program_type'
        ]

class InstitutionSerializer(serializers.ModelSerializer):
    program_types = ProgramTypeSerializer(many=True, read_only=True)
    program_type_ids = serializers.PrimaryKeyRelatedField(
        queryset=ProgramType.objects.all(), source='program_types', many=True, write_only=True, required=False
    )
    courses = CourseOfStudySerializer(many=True, read_only=True)
    country = serializers.SerializerMethodField()

    class Meta:
        model = Institution
        fields = [
            'id', 'name', 'country', 'city', 
            'email_address', 'address', 'website', 'program_types', 'program_type_ids', 'courses'
        ]

    def get_country(self, obj):
        # obj.country is a Country object from django-countries
        return obj.country.name if obj.country else None

class CourseOfStudyDetailSerializer(serializers.ModelSerializer):
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

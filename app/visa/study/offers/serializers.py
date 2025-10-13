from rest_framework import serializers
from app.visa.study.offers.models import StudyVisaOffer, StudyVisaOfferRequirement

class StudyVisaOfferRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyVisaOfferRequirement
        fields = [
            'id',
            'requirement',
            'is_mandatory',
            'notes',
        ]

class StudyVisaOfferSerializer(serializers.ModelSerializer):
    requirements = StudyVisaOfferRequirementSerializer(many=True, read_only=True)
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    course_of_study_name = serializers.CharField(source='course_of_study.name', read_only=True)
    program_type_name = serializers.CharField(source='program_type.name', read_only=True)
    status_display = serializers.CharField(source='status.value', read_only=True, default=None)

    class Meta:
        model = StudyVisaOffer
        fields = [
            'id',
            'institution',
            'institution_name',
            'course_of_study',
            'course_of_study_name',
            'program_type',
            'program_type_name',
            'country',
            'offer_title',
            'description',
            'tuition_fee',
            'application_deadline',
            'start_date',
            'end_date',
            'is_active',
            'created_at',
            'updated_at',
            'minimum_qualification',
            'minimum_grade',
            'english_proficiency_required',
            'english_test_type',
            'minimum_english_score',
            'other_requirements',
            'status',
            'status_display',
            'requirements',
            'status_name',
        ]

        read_only_fields = [
            'status_name',

        ]

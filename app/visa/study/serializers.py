from rest_framework import serializers
from .models import StudyVisaApplication


class StudyVisaApplicationSerializer(serializers.ModelSerializer):
    country = serializers.CharField(source="country_str", read_only=True)
    destination_country = serializers.SerializerMethodField()

    class Meta:
        model = StudyVisaApplication
        fields = [
            'id',
            # 1️⃣ Personal Information
            'applicant',
            'study_visa_offer',
            'passport_number',
            'country',
            'passport_expiry_date',

            # 2️⃣ Educational Background
            'highest_qualification',
            'previous_university',
            'previous_course_of_study',
            'cgpa_grade',
            'year_of_graduation',

            # 3️⃣ Visa & Study Details
            'destination_country',
            'institution',
            'course_of_study',
            'program_type',
            'intended_start_date',
            'intended_end_date',
            'visa_type',
            'sponsorship_details',

            # 4️⃣ Document Uploads
            'passport_photo',
            'international_passport',
            'academic_transcripts',
            'admission_letter',
            'financial_statement',
            'english_proficiency_test',

            # 5️⃣ Additional Information
            'previous_visa_applications',
            'previous_visa_details',
            'travel_history',
            'emergency_contact_name',
            'emergency_contact_relationship',
            'emergency_contact_phone',
            'statement_of_purpose',

            # 6️⃣ Review & Submit
            'is_submitted',
            'submitted_at',

            # System fields
            'application_date',
            'status',
            'notes',
        ]
        read_only_fields = ['application_date', 'status', 'submitted_at']

    def get_destination_country(self, obj):
        # Always return a string or None for JSON serialization
        if obj.destination_country:
            return str(obj.destination_country)
        return None

    def create(self, validated_data):
        # status is handled in model save() if not provided
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


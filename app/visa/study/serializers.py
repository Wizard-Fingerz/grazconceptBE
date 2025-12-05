from rest_framework import serializers
from .models import StudyVisaApplication, StudyVisaApplicationComment


class StudyVisaApplicationSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()
    # country = serializers.SerializerMethodField(source="country_str", read_only=True)
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
            'cgpa',
            'graduation_year',

            # 3️⃣ Visa & Study Details
            'destination_country',
            'institution',
            'course_of_study',
            'program_type',
            'intended_start_date',
            'intended_end_date',
            'visa_type',
            'sponsorship',

            # 4️⃣ Document Uploads
            'passport_photo',
            'passport_document',
            'academic_transcript',
            'admission_letter',
            'financial_statement',
            'english_test_result',

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
            'institution_name',
            'course_of_study_name',
            'program_type_name',
            'status_name',
        ]
        extra_kwargs = {
            'applicant': {'read_only': True},  # 👈 make it read-only
        }
        read_only_fields = ['application_date', 'status', 'submitted_at', 
            'institution_name',
            'course_of_study_name',
            'program_type_name',
            'status_name',]

    def get_destination_country(self, obj):
        # obj.country is a Country object from django-countries
        return obj.destination_country.name if obj.destination_country else None

    def get_country(self, obj):
        # obj.country is a Country object from django-countries
        return obj.country.name if obj.country else None

    def create(self, validated_data):
        # status is handled in model save() if not provided
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)




# Work Visa Application Comment Serializer
class StudyVisaApplicationCommentSerializer(serializers.ModelSerializer):
    sender_type = serializers.CharField(read_only=True)
    sender_display = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = StudyVisaApplicationComment
        fields = [
            "id",
            "visa_application",
            "applicant",
            "admin",
            "text",
            "created_at",
            "is_read_by_applicant",
            "is_read_by_admin",
            "attachment",
            "sender_type",
            "sender_display",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "sender_type",
            "sender_display",
        ]

    def get_sender_display(self, obj):
        # Replicate logic from sender_display property in the model
        if obj.applicant:
            return {
                "type": "applicant",
                "name": getattr(obj.applicant, "get_full_name", lambda: None)() or getattr(getattr(obj.applicant, "user", None), "username", None),
                "id": obj.applicant.id,
            }
        elif obj.admin:
            if hasattr(obj.admin, "get_full_name"):
                name = obj.admin.get_full_name()
            else:
                name = getattr(obj.admin, "username", None)
            return {
                "type": "admin",
                "name": name,
                "id": obj.admin.id,
            }
        return {"type": "unknown"}


from rest_framework import serializers
from app.visa.work.offers.models import (
    WorkVisaApplicationComment,
    WorkVisaOffer,
    WorkVisaOfferRequirement,
    WorkVisaApplication,
    # InterviewFAQ,
    WorkVisaInterview,
    CVSubmission,
)
from app.visa.work.organization.serializers import WorkOrganizationSerializer
from definition.models import TableDropDownDefinition


class WorkVisaOfferRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkVisaOfferRequirement
        fields = [
            'id',
            'description',
            'is_mandatory',
        ]
        read_only_fields = ['id']


class WorkVisaOfferSerializer(serializers.ModelSerializer):
    organization = WorkOrganizationSerializer(read_only=True)
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkVisaOffer._meta.get_field('organization').remote_field.model.objects.all(),
        source='organization',
        write_only=True
    )
    requirements = WorkVisaOfferRequirementSerializer(many=True, read_only=True)

    class Meta:
        model = WorkVisaOffer
        fields = [
            'id',
            'organization',
            'organization_id',
            'job_title',
            'job_description',
            'country',
            'city',
            'salary',
            'currency',
            'start_date',
            'end_date',
            'is_active',
            'created_at',
            'updated_at',
            'requirements',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']



# Work Visa Application Comment Serializer
class WorkVisaApplicationCommentSerializer(serializers.ModelSerializer):
    sender_type = serializers.CharField(read_only=True)
    sender_display = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = WorkVisaApplicationComment
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


class WorkVisaApplicationSerializer(serializers.ModelSerializer):
    offer = WorkVisaOfferSerializer(read_only=True)
    offer_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkVisaOffer.objects.all(),
        source='offer',
        write_only=True
    )
    status = serializers.SerializerMethodField()
    status_id = serializers.PrimaryKeyRelatedField(
        queryset=TableDropDownDefinition.objects.filter(table_name="work_visa_application_statuses", is_system_defined=True),
        source='status',
        write_only=True,
        required=False,
        allow_null=True
    )
    comments = WorkVisaApplicationCommentSerializer(many=True, read_only=True)

    # Serialize the country as a string (code), not as the Country object itself.
    country = serializers.SerializerMethodField()

    class Meta:
        model = WorkVisaApplication
        fields = [
            'id',
            'client',                     # FK
            'offer',
            'offer_id',
            # Step 1: Personal Information
            'passport_number',
            'country',
            'passport_expiry_date',
            'date_of_birth',
            'phone_number',
            # Step 2: Job Background
            'highest_degree',
            'years_of_experience',
            'previous_employer',
            'previous_job_title',
            'year_left_previous_job',
            # Step 3: Work Visa Details
            'intended_start_date',
            'intended_end_date',
            'visa_type',
            'sponsorship_details',
            "comments",
            # Step 4: Document Uploads
            'passport_photo',
            'international_passport',
            'updated_resume',
            'reference_letter',
            'employment_letter',
            'financial_statement',
            'english_proficiency_test',
            # Step 5: Additional Information
            'previous_visa_applications',
            'previous_visa_details',
            'travel_history',
            'emergency_contact_name',
            'emergency_contact_relationship',
            'emergency_contact_phone',
            'statement_of_purpose',
            # Deprecated/legacy fields
            'resume',
            'cover_letter',
            'passport_document',
            # Application meta/state
            'submitted_at',
            'status',
            'status_id',
            'admin_note',
        ]
        read_only_fields = [
            'id',
            'submitted_at',
            'offer',
            "comments",
            'status',
        ]

    def get_status(self, obj):
        if obj.status:
            return {
                'id': obj.status.id,
                'term': obj.status.term
            }
        return None

    def get_country(self, obj):
        # Return the country code as a string, or None if not set.
        if obj.country:
            return str(obj.country)
        return None

    def to_internal_value(self, data):
        """
        This override ensures that 'country' can be accepted as a string code in input.
        """
        ret = super().to_internal_value(data)
        country_value = data.get('country')
        if country_value is not None:
            ret['country'] = country_value
        return ret


# class InterviewFAQSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InterviewFAQ
#         fields = [
#             'id',
#             'question',
#             'answer',
#             'is_active',
#         ]
#         read_only_fields = ['id']


class WorkVisaInterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkVisaInterview
        fields = [
            'id',
            'application',
            'job_role',
            'country',
            'interview_date',
            'interview_time',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CVSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVSubmission
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'country',
            'job',
            'job_title_freeform',
            'skills',
            'other_skills',
            'cv_file',
            'cover_letter',
            'submitted_at',
            'updated_at',
            'is_processed',
        ]
        read_only_fields = [
            'id',
            'submitted_at',
            'updated_at',
        ]


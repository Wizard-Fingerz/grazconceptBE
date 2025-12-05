from django.conf import settings
from django.db import models
from account.client.models import Client
from app.visa.study.institutions.models import Institution, CourseOfStudy, ProgramType
from django_countries.fields import CountryField
from definition.models import TableDropDownDefinition
from app.visa.study.offers.models import StudyVisaOffer

from cloudinary.models import CloudinaryField

# Helper for file upload paths
def upload_to(instance, filename, prefix):
    return f'study_visa/{instance.id or "temp"}/{prefix}/{filename}'

class StudyVisaApplication(models.Model):
    """
    Represents a study visa application. Applicants can either apply directly to an institution
    or apply for a StudyVisaOffer (which may be a special program, scholarship, or bundled offer).
    If 'study_visa_offer' is set, the application is for that offer; otherwise, it's a direct application to an institution.
    """
    # 1️⃣ Personal Information
    applicant = models.ForeignKey('account.Client', on_delete=models.CASCADE, related_name='visa_applicants')
    # If the user is applying for a StudyVisaOffer, this is set; otherwise, it's null.
    study_visa_offer = models.ForeignKey(
        StudyVisaOffer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
        help_text="The Study Visa Offer selected for this application, if any."
    )

    passport_number = models.CharField(max_length=50, null=True, blank=True)
    passport_expiry_date = models.DateField(blank=True, null=True)
    country = CountryField(blank=True, null=True)

    # 2️⃣ Educational Background
    highest_qualification = models.CharField(max_length=255, blank=True, null=True)
    previous_university = models.CharField(max_length=255, blank=True, null=True)
    previous_course_of_study = models.CharField(max_length=255, blank=True, null=True)
    cgpa = models.CharField(max_length=20, blank=True, null=True)
    graduation_year = models.PositiveIntegerField(blank=True, null=True)

    # 3️⃣ Visa & Study Details

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='visa_applications',
        null=True,
        blank=True,
        help_text="Institution being applied to. If applying for a StudyVisaOffer, this may be set automatically."
    )
    course_of_study = models.ForeignKey(
        CourseOfStudy,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='visa_applications_course_of_study',
        help_text="Course of study. If applying for a StudyVisaOffer, this may be set automatically."
    )
    program_type = models.ForeignKey(
        ProgramType,
        on_delete=models.CASCADE,
        related_name='visa_applications_program_types',
        null=True,
        blank=True,
        help_text="Program type. If applying for a StudyVisaOffer, this may be set automatically."
    )
    intended_start_date = models.DateField(blank=True, null=True)
    intended_end_date = models.DateField(blank=True, null=True)
    visa_type = models.ForeignKey(
        'definition.TableDropDownDefinition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='study_visa_visa_types',
        limit_choices_to={'table_name': 'study_visa_type'},
        help_text="Visa type (e.g., Student, Exchange, Research) from TableDropDownDefinition."
    )
    sponsorship = models.ForeignKey(
        'definition.TableDropDownDefinition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='study_visa_sponsorship_details',
        limit_choices_to={'table_name': 'study_sponsorship_type'},
        help_text="Sponsorship details (e.g., Self-funded, Sponsored) from TableDropDownDefinition."
    )

    # 4️⃣ Document Uploads
    passport_photo = CloudinaryField('image', blank=True, null=True)
    passport_document = CloudinaryField('file', blank=True, null=True)
    academic_transcript = CloudinaryField('file', blank=True, null=True)
    admission_letter = CloudinaryField('file', blank=True, null=True)
    financial_statement = CloudinaryField('file', blank=True, null=True)
    english_test_result = CloudinaryField('file', blank=True, null=True)

    # 5️⃣ Additional Information
    previous_visa_applications = models.BooleanField(default=False)
    previous_visa_details = models.TextField(blank=True, null=True)
    travel_history = models.TextField(blank=True, null=True)  # Countries visited, Dates
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True, null=True)
    statement_of_purpose = CloudinaryField('file', blank=True, null=True)

    # 6️⃣ Review & Submit
    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add= True, blank=True, null=True)

    # System fields
    application_date = models.DateField(auto_now_add=True)
    status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='study_visa_status',
        limit_choices_to={'table_name': 'study_visa_status'},
        default=None  # Will be set in save()
    )
    notes = models.TextField(blank=True, null=True)
    
    @property
    def institution_name(self):
        return self.institution.name if self.institution else None

    @property
    def course_of_study_name(self):
        return self.course_of_study.name if self.course_of_study else None

    @property
    def program_type_name(self):
        return self.program_type.name if self.program_type else None

    @property
    def status_name(self):
        return self.status.term if self.status else None

    @property
    def country_str(self):
        if self.country:
            return str(self.country)
        return None

    @property
    def destination_country(self):
        if self.institution and hasattr(self.institution, 'country'):
            return self.institution.country
        elif (
            self.study_visa_offer
            and self.study_visa_offer.institution
            and hasattr(self.study_visa_offer.institution, 'country')
        ):
            return self.study_visa_offer.institution.country
        else:
            return None

    def all_required_fields_filled(self):
        """
        Returns True if all required fields for a 'Completed' application are filled, else False.
        """
        required_fields = [
            self.passport_number,
            self.passport_expiry_date,
            self.country,
            self.highest_qualification,
            self.previous_university,
            self.previous_course_of_study,
            self.cgpa,
            self.graduation_year,
            self.destination_country,  # property
            self.institution,
            self.course_of_study,
            self.program_type,
            self.intended_start_date,
            self.intended_end_date,
            self.visa_type,
            self.sponsorship,  # fixed from sponsorship_details
            self.passport_photo,
            self.passport_document,  # fixed from international_passport
            self.academic_transcript,  # fixed from academic_transcripts
            self.admission_letter,
            self.financial_statement,
            self.english_test_result,  # fixed from english_proficiency_test
            self.emergency_contact_name,
            self.emergency_contact_relationship,
            self.emergency_contact_phone,
            self.statement_of_purpose,
        ]
        for value in required_fields:
            if value is None:
                return False
            if isinstance(value, str) and value.strip() == "":
                return False
        return True

    def save(self, *args, **kwargs):
        from django.utils import timezone

        # If applying for a StudyVisaOffer, auto-populate institution/course/program_type if not set
        if self.study_visa_offer:
            offer = self.study_visa_offer
            if not self.institution:
                self.institution = offer.institution
            if not self.course_of_study:
                self.course_of_study = offer.course_of_study
            if not self.program_type:
                self.program_type = offer.program_type

        # Determine status based on completeness
        try:
            completed_status = TableDropDownDefinition.objects.get(
                term='Completed',
                table_name='study_visa_status'
            )
        except TableDropDownDefinition.DoesNotExist:
            completed_status = None

        try:
            draft_status = TableDropDownDefinition.objects.get(
                term='Draft',
                table_name='study_visa_status'
            )
        except TableDropDownDefinition.DoesNotExist:
            draft_status = None

        # Track status change
        old_status_id = None
        if self.pk:
            try:
                old = StudyVisaApplication.objects.get(pk=self.pk)
                old_status_id = old.status_id
            except StudyVisaApplication.DoesNotExist:
                old_status_id = None

        if self.all_required_fields_filled():
            if completed_status:
                self.status = completed_status
        else:
            if draft_status:
                self.status = draft_status

        # Set submitted_at if just submitted
        if self.is_submitted and self.submitted_at is None:
            self.submitted_at = timezone.now()
        super().save(*args, **kwargs)

        # Log status change if it changed, and include the date and time the status changed
        if self.status_id != old_status_id:
            StudyVisaApplicationStatusLog.objects.create(
                application=self,
                old_status_id=old_status_id,
                new_status=self.status,
                changed_at=timezone.now()
            )

    def __str__(self):
        if self.study_visa_offer:
            offer_title = self.study_visa_offer.offer_title
            institution_name = self.study_visa_offer.institution.name
            return f"{self.applicant.first_name} {self.applicant.last_name} - Offer: {offer_title} ({institution_name}) [{self.status}]"
        else:
            institution_name = self.institution.name if self.institution else "N/A"
            return f"{self.applicant.first_name} {self.applicant.last_name} - {institution_name} ({self.status})"

class StudyVisaApplicationStatusLog(models.Model):
    application = models.ForeignKey(StudyVisaApplication, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='old_study_visa_status_logs'
    )
    new_status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='new_study_visa_status_logs'
    )
    changed_at = models.DateTimeField()

    def __str__(self):
        return f"Application {self.application.id}: {self.old_status.term if self.old_status else 'None'} → {self.new_status.term if self.new_status else 'None'} at {self.changed_at}"




class StudyVisaApplicationComment(models.Model):
    """
    Communication comment between admin/agent and applicant for StudyVisaApplication.
    """
    visa_application = models.ForeignKey(
        StudyVisaApplication,
        related_name='comments',
        on_delete=models.CASCADE,
        help_text="The Work visa application this comment belongs to."
    )
    # Exactly one of applicant or admin should be SET for sender.
    applicant = models.ForeignKey(
        Client,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='study_application_comments_sent',
        help_text="Set if this comment is from the applicant."
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='study_visa_application_comments_admin',
        help_text="Set if this comment is from an admin/agent user."
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read_by_applicant = models.BooleanField(default=False)
    is_read_by_admin = models.BooleanField(default=False)
    # (optional) Document upload to clarify/request something
    attachment = CloudinaryField(
        'auto',
        blank=True,
        null=True,
        help_text="Optional file/document related to this comment."
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        if self.applicant:
            sender = self.applicant.get_full_name() or (self.applicant.user.username if hasattr(self.applicant, "user") and self.applicant.user else str(self.applicant.pk))
            sender_type = "Applicant"
        elif self.admin:
            # Prefer get_full_name if present, fall back to username, otherwise pk
            if hasattr(self.admin, 'get_full_name'):
                sender = self.admin.get_full_name()
            elif hasattr(self.admin, 'username'):
                sender = self.admin.username
            else:
                sender = str(self.admin.pk)
            sender_type = "Admin"
        else:
            sender = "Unknown"
            sender_type = "Unknown"
        return f"Comment by {sender_type}: {sender} on application {self.visa_application.id}"

    @property
    def sender_type(self):
        if self.applicant and self.admin:
            return "applicant+admin"
        elif self.applicant:
            return "applicant"
        elif self.admin:
            return "admin"
        return "unknown"

    @property
    def sender_display(self):
        """
        For serializers/UI, show info about who sent the comment.
        """
        if self.applicant:
            name = self.applicant.get_full_name()
            if not name and hasattr(self.applicant, "user") and self.applicant.user:
                name = self.applicant.user.username
            return {
                "type": "applicant",
                "name": name or str(self.applicant.pk),
                "id": self.applicant.id,
            }
        elif self.admin:
            name = ""
            if hasattr(self.admin, 'get_full_name'):
                name = self.admin.get_full_name()
            elif hasattr(self.admin, 'username'):
                name = self.admin.username
            else:
                name = str(self.admin.pk)
            return {
                "type": "admin",
                "name": name,
                "id": self.admin.id,
            }
        return {"type": "unknown"}


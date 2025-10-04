from django.db import models
from account.client.models import Client
from app.visa.study.institutions.models import Institution, CourseOfStudy, ProgramType
from django_countries.fields import CountryField
from definition.models import TableDropDownDefinition
from app.visa.study.offers.models import StudyVisaOffer

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
    cgpa_grade = models.CharField(max_length=20, blank=True, null=True)
    year_of_graduation = models.PositiveIntegerField(blank=True, null=True)

    # 3️⃣ Visa & Study Details
    destination_country = CountryField(blank=True, null=True)
    # If applying for a StudyVisaOffer, institution/course/program_type can be null and inferred from the offer.
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
    visa_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., Student, Exchange, Research
    sponsorship_details = models.CharField(max_length=100, blank=True, null=True)  # Self-funded / Sponsored

    # 4️⃣ Document Uploads
    passport_photo = models.ImageField(upload_to='study_visa/passport_photos/', blank=True, null=True)
    international_passport = models.FileField(upload_to='study_visa/international_passports/', blank=True, null=True)
    academic_transcripts = models.FileField(upload_to='study_visa/academic_transcripts/', blank=True, null=True)
    admission_letter = models.FileField(upload_to='study_visa/admission_letters/', blank=True, null=True)
    financial_statement = models.FileField(upload_to='study_visa/financial_statements/', blank=True, null=True)
    english_proficiency_test = models.FileField(upload_to='study_visa/english_proficiency/', blank=True, null=True)

    # 5️⃣ Additional Information
    previous_visa_applications = models.BooleanField(default=False)
    previous_visa_details = models.TextField(blank=True, null=True)
    travel_history = models.TextField(blank=True, null=True)  # Countries visited, Dates
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True, null=True)
    statement_of_purpose = models.TextField(blank=True, null=True)

    # 6️⃣ Review & Submit
    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(blank=True, null=True)

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
    def country_str(self):
        # Always return a string or None for JSON serialization
        if self.country:
            return str(self.country)
        return None

    def save(self, *args, **kwargs):
        # If applying for a StudyVisaOffer, auto-populate institution/course/program_type if not set
        if self.study_visa_offer:
            offer = self.study_visa_offer
            if not self.institution:
                self.institution = offer.institution
            if not self.course_of_study:
                self.course_of_study = offer.course_of_study
            if not self.program_type:
                self.program_type = offer.program_type
            if not self.destination_country:
                self.destination_country = offer.country

        if self.status is None:
            try:
                self.status = TableDropDownDefinition.objects.get(
                    term='Pending',
                    table_name='study_visa_status'
                )
            except TableDropDownDefinition.DoesNotExist:
                self.status = None
        # Set submitted_at if just submitted
        if self.is_submitted and self.submitted_at is None:
            from django.utils import timezone
            self.submitted_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        # Show offer title if applying for an offer, else show institution
        if self.study_visa_offer:
            offer_title = self.study_visa_offer.offer_title
            institution_name = self.study_visa_offer.institution.name
            return f"{self.applicant.first_name} {self.applicant.last_name} - Offer: {offer_title} ({institution_name}) [{self.status}]"
        else:
            institution_name = self.institution.name if self.institution else "N/A"
            return f"{self.applicant.first_name} {self.applicant.last_name} - {institution_name} ({self.status})"

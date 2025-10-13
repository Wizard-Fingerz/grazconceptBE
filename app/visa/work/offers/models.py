from django.db import models
from django_countries.fields import CountryField
from app.visa.work.organization.models import WorkOrganization
from account.client.models import Client
from definition.models import TableDropDownDefinition

def get_default_work_visa_status():
    try:
        return TableDropDownDefinition.objects.get(
            term="Draft",
            table_name="work_visa_application_statuses",
            is_system_defined=True
        ).id
    except Exception:
        return None

class WorkVisaOfferRequirement(models.Model):
    """
    Model to store requirements for a work visa offer.
    """
    offer = models.ForeignKey(
        'WorkVisaOffer',
        on_delete=models.CASCADE,
        related_name='requirements',
        help_text="The work visa offer this requirement belongs to"
    )
    description = models.CharField(
        max_length=255,
        help_text="Description of the requirement"
    )
    is_mandatory = models.BooleanField(
        default=True,
        help_text="Is this requirement mandatory?"
    )

    class Meta:
        verbose_name = "Work Visa Offer Requirement"
        verbose_name_plural = "Work Visa Offer Requirements"

    def __str__(self):
        return f"{self.description} ({'Mandatory' if self.is_mandatory else 'Optional'})"

class WorkVisaOffer(models.Model):
    """
    Model to store job offers for work visa applications.
    """
    organization = models.ForeignKey(
        WorkOrganization,
        on_delete=models.CASCADE,
        related_name='visa_offers',
        help_text="The organization offering the job"
    )
    job_title = models.CharField(
        max_length=255,
        help_text="Title of the job position"
    )
    job_description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of the job role"
    )
    country = CountryField(
        help_text="Country where the job is located"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="City where the job is located"
    )
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Offered salary (if specified)"
    )
    currency = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Currency of the salary (e.g., USD, EUR)"
    )
    start_date = models.DateField(
        blank=True,
        null=True,
        help_text="Proposed start date for the job"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="End date of the contract (if applicable)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this offer currently active?"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Work Visa Offer"
        verbose_name_plural = "Work Visa Offers"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.job_title} at {self.organization.name}"


class WorkVisaApplication(models.Model):
    """
    Model to store a client's application for a specific work visa job offer.
    The application can collect both job-related and visa-related info.
    The 'country' (nationality) is automatically filled from the client model's country.
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="work_visa_applications",
        help_text="Client applying for the work visa"
    )
    offer = models.ForeignKey(
        WorkVisaOffer,
        on_delete=models.CASCADE,
        related_name="applications",
        help_text="The specific job offer the client is applying to"
    )

    # Step 1: Personal Information
    passport_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Applicant's passport number"
    )
    country = CountryField(
        blank=True,
        null=True,
        help_text="Applicant's nationality country (auto filled from client)"
    )
    passport_expiry_date = models.DateField(
        blank=True,
        null=True,
        help_text="Passport expiry date"
    )

    # Step 2: Job Background
    highest_degree = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Applicant's highest degree obtained"
    )
    years_of_experience = models.IntegerField(
        blank=True,
        null=True,
        help_text="Total years of work experience"
    )
    previous_employer = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Previous employer name"
    )
    previous_job_title = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Job title at previous employer"
    )
    year_left_previous_job = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Year applicant left previous job"
    )

    # Step 3: Work Visa Details
    intended_start_date = models.DateField(
        blank=True,
        null=True,
        help_text="Intended start date for work visa"
    )
    intended_end_date = models.DateField(
        blank=True,
        null=True,
        help_text="Intended end date for work visa"
    )
    visa_type = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Requested visa type"
    )
    sponsorship_details = models.TextField(
        blank=True,
        null=True,
        help_text="Details about sponsorship (if applicable)"
    )

    # Step 4: Document Uploads
    passport_photo = models.FileField(
        upload_to="work_visa_applications/passport_photo/",
        blank=True,
        null=True,
        help_text="Passport sized recent photo"
    )
    international_passport = models.FileField(
        upload_to="work_visa_applications/international_passport/",
        blank=True,
        null=True,
        help_text="Scanned international passport document"
    )
    updated_resume = models.FileField(
        upload_to="work_visa_applications/resume/",
        blank=True,
        null=True,
        help_text="Updated Resume/CV"
    )
    reference_letter = models.FileField(
        upload_to="work_visa_applications/reference_letter/",
        blank=True,
        null=True,
        help_text="Reference letter upload"
    )
    employment_letter = models.FileField(
        upload_to="work_visa_applications/employment_letter/",
        blank=True,
        null=True,
        help_text="Employment letter upload"
    )
    financial_statement = models.FileField(
        upload_to="work_visa_applications/financial_statement/",
        blank=True,
        null=True,
        help_text="Financial/bank statement"
    )
    english_proficiency_test = models.FileField(
        upload_to="work_visa_applications/english_proficiency/",
        blank=True,
        null=True,
        help_text="Proof of English language proficiency"
    )

    # Step 5: Additional Information
    previous_visa_applications = models.BooleanField(
        blank=True,
        null=True,
        help_text="Has applicant previously applied for a visa?"
    )
    previous_visa_details = models.TextField(
        blank=True,
        null=True,
        help_text="Details about previous visa applications"
    )
    travel_history = models.TextField(
        blank=True,
        null=True,
        help_text="Brief travel history"
    )
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Emergency contact name"
    )
    emergency_contact_relationship = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Relationship to emergency contact"
    )
    emergency_contact_phone = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Emergency contact phone number"
    )
    statement_of_purpose = models.TextField(
        blank=True,
        null=True,
        help_text="Applicant's statement of purpose for application"
    )

    # Deprecated/legacy fields or moved fields
    resume = models.FileField(
        upload_to='work_visa_applications/legacy_resume/',
        blank=True,
        null=True,
        help_text="(Legacy) Resume or CV document"
    )
    cover_letter = models.TextField(
        blank=True,
        null=True,
        help_text="(Legacy) Cover letter for the job application"
    )
    passport_document = models.FileField(
        upload_to='work_visa_applications/legacy_passport/',
        blank=True,
        null=True,
        help_text="(Legacy) Scanned passport document"
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="Applicant's date of birth"
    )
    phone_number = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Applicant's contact phone number"
    )

    # Application state
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date/time the application was submitted"
    )

    status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="work_visa_application_statuses",
        help_text="Current status of the application",
        default=get_default_work_visa_status,
    )
    
    # Optional: Note for admin or reviewer
    admin_note = models.TextField(
        blank=True,
        null=True,
        help_text="Note for internal review or admin"
    )

    class Meta:
        verbose_name = "Work Visa Application"
        verbose_name_plural = "Work Visa Applications"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Application of {self.client} for {self.offer}"

    def save(self, *args, **kwargs):
        # Auto-fill country from the client if possible
        if self.client and hasattr(self.client, "country"):
            if not self.country or self.country != self.client.country:
                self.country = self.client.country
        super().save(*args, **kwargs)


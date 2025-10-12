from django.db import models
from django_countries.fields import CountryField
from app.visa.work.organization.models import WorkOrganization
from account.client.models import Client
from definition.models import TableDropDownDefinition


def get_default_work_visa_status():
    # Tries to fetch the TableDropDownDefinition with term "Draft" for work_visa_application_statuses
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
    # Job-specific information (CV/resume, cover letter, etc.)
    resume = models.FileField(
        upload_to='work_visa_applications/resume/',
        blank=True,
        null=True,
        help_text="Resume or CV document"
    )
    cover_letter = models.TextField(
        blank=True,
        null=True,
        help_text="Cover letter for the job application"
    )
    # Visa-required information (passport, etc.)
    passport_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Applicant's passport number"
    )
    passport_document = models.FileField(
        upload_to='work_visa_applications/passport/',
        blank=True,
        null=True,
        help_text="Scanned passport document"
    )
    nationality = CountryField(
        blank=True,
        null=True,
        help_text="Applicant's nationality"
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

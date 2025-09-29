from django.db import models
from django_countries.fields import CountryField
from app.visa.work.organization.models import WorkOrganization

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

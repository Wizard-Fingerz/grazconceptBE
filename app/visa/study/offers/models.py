from django.db import models
from app.visa.study.institutions.models import Institution, CourseOfStudy, ProgramType
from django_countries.fields import CountryField
from definition.models import TableDropDownDefinition

class StudyVisaOffer(models.Model):
    """
    Represents a study visa offer available to applicants, including its requirements.
    """
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='study_visa_offers'
    )
    course_of_study = models.ForeignKey(
        CourseOfStudy,
        on_delete=models.CASCADE,
        related_name='study_visa_offers'
    )
    program_type = models.ForeignKey(
        ProgramType,
        on_delete=models.CASCADE,
        related_name='study_visa_offers'
    )
    country = CountryField(blank=True, null=True)
    offer_title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    tuition_fee = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    application_deadline = models.DateField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Requirements
    minimum_qualification = models.CharField(max_length=255, blank=True, null=True)
    minimum_grade = models.CharField(max_length=50, blank=True, null=True)
    english_proficiency_required = models.BooleanField(default=False)
    english_test_type = models.CharField(max_length=100, blank=True, null=True)  # e.g., IELTS, TOEFL
    minimum_english_score = models.CharField(max_length=50, blank=True, null=True)
    other_requirements = models.TextField(blank=True, null=True)

    # Status (e.g., Open, Closed, Waitlist)
    status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='study_visa_offer_status',
        limit_choices_to={'table_name': 'study_visa_offer_status'},
        default=None
    )

    @property
    def status_name(self):
        return self.status.name

    def __str__(self):
        return f"{self.offer_title} - {self.institution.name} ({self.course_of_study.name})"

class StudyVisaOfferRequirement(models.Model):
    """
    Additional requirements for a StudyVisaOffer (e.g., specific documents, conditions).
    """
    offer = models.ForeignKey(
        StudyVisaOffer,
        on_delete=models.CASCADE,
        related_name='requirements'
    )
    requirement = models.CharField(max_length=255)
    is_mandatory = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.requirement} ({'Mandatory' if self.is_mandatory else 'Optional'})"

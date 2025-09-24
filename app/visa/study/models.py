from django.db import models
from account.client.models import Client
from app.visa.study.institutions.models import Institution, CourseOfStudy, ProgramType
from django_countries.fields import CountryField

from definition.models import TableDropDownDefinition


class StudyVisaApplication(models.Model):
    applicant = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='visa_applicants')
    passport_number = models.CharField(max_length=50, null = True, blank = True)
    country = CountryField()
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='visa_applications')
    course_of_study = models.ForeignKey(CourseOfStudy, null = True, blank = True, on_delete=models.CASCADE, related_name='visa_applications_course_of_study')
    program_type = models.ForeignKey(ProgramType, on_delete=models.CASCADE, related_name='visa_applications_program_types')
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

    def save(self, *args, **kwargs):
        if self.status is None:
            try:
                self.status = TableDropDownDefinition.objects.get(
                    term='Pending',
                    table_name='study_visa_status'
                )
            except TableDropDownDefinition.DoesNotExist:
                self.status = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.applicant_name} - {self.institution.name} ({self.status})"
